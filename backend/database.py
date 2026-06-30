import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

def get_connection():
    conn = psycopg.connect(
        host = os.getenv("POSTGRES_HOST"),
        port = os.getenv("POSTGRES_PORT"),
        dbname = os.getenv("POSTGRES_DB"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD")   
    )
    return conn

def get_raw_schema():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        select table_name, column_name, data_type
        from information_schema.columns
        where table_schema = 'public'
        order by table_name, ordinal_position;    
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_foreign_keys():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public';
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_sample_values(table, column, limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT {column} FROM {table} LIMIT %s;", (limit,))
    values = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return values

if __name__ == "__main__":
    # conn = get_connection()
    conn = get_raw_schema()
    print("Working with schema:", conn)
    fks = get_foreign_keys()
    print("Foreign keys:", fks)