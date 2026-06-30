from database import get_raw_schema, get_foreign_keys, get_connection, get_sample_values
import os
from groq import Groq
from decimal import Decimal
import sqlglot
from sqlglot import exp

SYSTEM_PROMPT_TEMPLATE = """You are a PostgreSQL expert that converts natural language questions into SQL queries.

Here is the database schema:

{schema}

Rules:
1. Only generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or any statement that modifies data or schema.
2. Always include a LIMIT clause capped at 20 rows, unless the user explicitly asks for a different number of rows.
3. Output ONLY the raw SQL query. No markdown code fences, no explanations, no commentary before or after.
4. Use only the tables and columns shown in the schema above. Do not invent or assume columns that are not listed.
5. If the question cannot be answered using this schema, respond with exactly: UNANSWERABLE
6. You may use aggregate functions, JOINs, window functions, GROUP BY, and CASE WHEN freely — these are fully supported.
7. When using window functions like LAG/LEAD combined with aggregates (e.g. COUNT, SUM) over grouped data, compute the aggregate in a subquery or CTE first, then apply the window function on top of that subquery's result — never mix raw GROUP BY columns and window functions referencing ungrouped columns in the same SELECT level.
"""

def build_schema_dict(raw_schema):
    schema_dict = {}
    for table, column, dtype in raw_schema:
        if table not in schema_dict:
            schema_dict[table] = []
        schema_dict[table].append((column, dtype))
    return schema_dict

CATEGORICAL_COLUMNS = {
    "customers": ["customer_state", "customer_city"],
    "sellers": ["seller_state", "seller_city"],
    "orders": ["order_status"],
    "order_payments": ["payment_type"],
    "products": ["product_category_name"],
}

COLUMN_NOTES = {
    ("customers", "customer_id"): "unique per order, NOT per person",
    ("customers", "customer_unique_id"): "unique per actual person — use this to identify repeat customers",
}

def format_as_ddl(schema_dict, foreign_keys):
    ddl_blocks = []

    for table_name, columns in schema_dict.items():
        lines = []
        for col_name, dtype in columns:
            line = f"    {col_name} {dtype}"

            note_parts = []
            if (table_name, col_name) in COLUMN_NOTES:
                note_parts.append(COLUMN_NOTES[(table_name, col_name)])
            if table_name in CATEGORICAL_COLUMNS and col_name in CATEGORICAL_COLUMNS[table_name]:
                samples = get_sample_values(table_name, col_name, limit=10)
                note_parts.append(f"e.g. {', '.join(str(s) for s in samples)}")

            if note_parts:
                line += "  -- " + "; ".join(note_parts)

            lines.append(line)

        table_fks = [fk for fk in foreign_keys if fk[0] == table_name]
        for source_table, source_col, target_table, target_col in table_fks:
            lines.append(f"    FOREIGN KEY ({source_col}) REFERENCES {target_table}({target_col})")

        block = f"CREATE TABLE {table_name} (\n" + ",\n".join(lines) + "\n);"
        ddl_blocks.append(block)

    return "\n\n".join(ddl_blocks)

def get_schema_context():
    raw = get_raw_schema()
    schema_dict = build_schema_dict(raw)
    fks = get_foreign_keys()
    return format_as_ddl(schema_dict, fks)

def generate_sql(question):
    schema = get_schema_context()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(schema=schema)
    client = Groq(api_key = os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model = "openai/gpt-oss-120b",
        messages = [
            {"role" : "system", "content": system_prompt},
            {"role" : "user", "content": question}
        ]
    )
    return response.choices[0].message.content.strip()

def execute_query(sql):
    if sql.strip().upper() == "UNANSWERABLE":
        return {"error": "This question cannot be answered with the available data."}
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    results = []
    for row in rows:
        clean_row = {}
        for col, value in zip(columns, row):
            if isinstance(value, Decimal):
                value = float(value)
            clean_row[col] = value
        results.append(clean_row)
    cur.close()
    conn.close()
    return results

def validate_sql(sql):
    raw = get_raw_schema()
    valid_tables = {row[0] for row in raw}
    valid_columns = {row[1] for row in raw}

    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
    except Exception as e:
        return False, f"SQL failed to parse: {e}"

    tables_used = {t.name for t in parsed.find_all(exp.Table)}
    columns_used = {c.name for c in parsed.find_all(exp.Column)}
    aliases_defined = {a.alias for a in parsed.find_all(exp.Alias) if a.alias}
    ctes_defined = {c.alias for c in parsed.find_all(exp.CTE) if c.alias}

    tables_to_check = tables_used - ctes_defined
    columns_to_check = columns_used - aliases_defined

    unknown_tables = tables_to_check - valid_tables
    unknown_columns = columns_to_check - valid_columns

    if unknown_tables:
        return False, f"Unknown table(s): {unknown_tables}"
    if unknown_columns:
        return False, f"Unknown column(s): {unknown_columns}"

    return True, "Valid"

def answer_question(question):
    sql = generate_sql(question)
    if sql.strip().upper() == "UNANSWERABLE":
        return {"status": "unanswerable", "message": "This question cannot be answered with the available data."}
    is_valid, validation_message = validate_sql(sql)
    if not is_valid:
        return {"status": "invalid_sql", "message": validation_message, "sql": sql}
    
    try:
        results = execute_query(sql)
    except Exception as e:
        return {"status": "execution_error", "message": str(e), "sql": sql}
    
    return {"status": "success", "sql": sql, "results": results}
    
import time

if __name__ == "__main__":
    spot_checks = [
        "What are the top 10 sellers by total revenue?",                              # unrelated table, untouched by changes
        "For each customer state, what is the total amount spent?",                   # touches customers table, but not uniqueness logic
        "Rank sellers by total sales within each state using a window function.",      # window function, but no LAG/CTE pattern
        "What is the current stock level for product category electronics?",          # should still be UNANSWERABLE
        "Which customers have placed more than 3 orders?",                            # retest of the flaky one, second data point
    ]

    for i, q in enumerate(spot_checks, start=1):
        print(f"\n--- Spot Check {i}: {q} ---")
        result = answer_question(q)
        print("Status:", result.get("status"))
        if result.get("status") == "success":
            print("SQL:", result["sql"].replace("\n", " "))
            print("Sample result:", result["results"][:3])
        else:
            print("Message:", result.get("message"))