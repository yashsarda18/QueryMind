# QueryMind — Decision Log

## Architecture Decisions

### D001 — PostgreSQL over other databases
Date: 2026-06-29
Context: Needed a production-grade relational database for storing 100k+ Olist orders
Decision: PostgreSQL 15 running in Docker
Alternatives considered: SQLite (too lightweight, not production-grade), MySQL (less feature-rich)
Tradeoffs: Slightly more setup than SQLite but industry standard at every target company
Interview talking point: "I chose PostgreSQL because it's what Atlassian, Xero and REA Group 
run in production — I wanted the project to reflect real engineering decisions, not shortcuts."

### D002 — Docker Compose for all services
Date: 2026-06-29
Context: Project needs PostgreSQL, Redis, FastAPI and frontend running together
Decision: Docker Compose with all 4 services defined in one file
Alternatives considered: Running services manually on host machine
Tradeoffs: Slightly more upfront setup, but one-command startup and identical behaviour 
across local and production environments
Interview talking point: "I containerised everything from Day 1 so the project spins up 
with one command — docker-compose up. That's what production-ready means to me."

### D003 — PostgreSQL volume for data persistence
Date: 2026-06-29
Context: Docker containers are stateless by default — data disappears on restart
Decision: Named volume postgres_data mounted to /var/lib/postgresql/data
Alternatives considered: Bind mount to local folder (messier, permission issues on Windows)
Tradeoffs: Named volumes are managed by Docker, cleaner and more portable
Interview talking point: "Without the volume, every restart would wipe 100k rows of data. 
Understanding stateless containers vs persistent storage is fundamental to production systems."

### D004 — Redis for query result caching
Date: 2026-06-29
Context: Every natural language query hits the LLM (3s latency) and PostgreSQL — expensive
Decision: Cache query results in Redis keyed on MD5 hash of the NL input, TTL of 1 hour
Alternatives considered: In-memory Python dict (lost on restart), PostgreSQL cache table (too slow)
Tradeoffs: Cache invalidation not needed here since dataset is static
Interview talking point: "I noticed repeated queries were hitting the LLM every time — 
added Redis cache keyed on MD5 hash of NL input. Dropped latency from ~3s to under 50ms 
on cache hits. That's the difference between a demo and a product."

### D005 — Groq with Llama 3.1 70B for SQL generation
Date: 2026-06-29
Context: Need an LLM to convert natural language to SQL reliably and fast
Decision: Groq API with Llama 3.1 70B
Alternatives considered: OpenAI GPT-4 (expensive, slower), local Ollama (too slow for demo)
Tradeoffs: Groq is free tier with generous limits, sub-second inference
Interview talking point: "I chose Groq because latency matters for a live demo — 
Groq's inference speed made the product feel responsive, not like a research prototype."

> **Superseded by D016** — see below. Llama 3.1/3.3 70B were deprecated by Groq; migrated to openai/gpt-oss-120b.

### D006 — XGBoost for delivery delay classifier
Date: 2026-06-29
Context: Need ML model to predict whether an order will be delivered late
Decision: XGBoost binary classifier with class_weight='balanced'
Alternatives considered: PyTorch MLP (overkill for tabular), logistic regression (too simple)
Tradeoffs: XGBoost is interpretable via feature importance, fast to train, strong on tabular data
Interview talking point: "I chose XGBoost over a neural network because the data is tabular 
and structured — tree-based models consistently outperform deep learning on this data type. 
Feature importance also gives me explainability, which matters for business users."

### D007 — class_weight='balanced' for class imbalance
Date: 2026-06-29
Context: Only 8.11% of orders are late — severe class imbalance
Decision: Use scale_pos_weight in XGBoost to balance classes during training
Alternatives considered: SMOTE oversampling, undersampling majority class
Tradeoffs: scale_pos_weight is simpler and works well with XGBoost specifically
Interview talking point: "If I trained without handling class imbalance, the model would 
predict 'on time' for everything and achieve 91.89% accuracy while being completely useless. 
I used F1 score and precision/recall as metrics instead of accuracy."

### D008 — Next.js + shadcn/ui + Tailwind for frontend
Date: 2026-06-29
Context: Need a polished UI for demos and interviews — Streamlit looks like a student project
Decision: Next.js with shadcn/ui components and Tailwind CSS
Alternatives considered: Streamlit (not professional enough), raw React (too steep learning curve)
Tradeoffs: More setup than Streamlit but the result looks like a real SaaS product
Interview talking point: "I deliberately chose Next.js over Streamlit because I wanted the 
project to look like something I'd ship to real users, not a data science notebook."

### D009 — Prediction logging to PostgreSQL
Date: 2026-06-29
Context: Need to track ML model predictions for monitoring and future retraining
Decision: Log every prediction (input features, prediction, confidence) to a PostgreSQL table
Alternatives considered: MLflow (overkill for this scope), Grafana (too much infrastructure)
Tradeoffs: Simple, no extra services, queryable with SQL
Interview talking point: "I logged every prediction to PostgreSQL so I can query prediction 
history, monitor for drift, and use real traffic data to retrain the model later."

### D010 — psycopg3 over psycopg2 for database driver
Date: 2026-06-30
Context: Needed a Python driver to connect to PostgreSQL for schema introspection and query execution
Decision: psycopg3 (`psycopg` package)
Alternatives considered: psycopg2 (more established, sync-only), SQLAlchemy (ORM, too much abstraction for raw dynamic SQL execution)
Tradeoffs: Slightly less mature ecosystem than psycopg2, but native async support via `psycopg.AsyncConnection` avoids a refactor when FastAPI (Day 3) needs async database calls
Interview talking point: "I chose psycopg3 over the more common psycopg2 because I knew Day 3 would need async FastAPI endpoints — picking the async-native driver upfront avoided a rewrite later."

### D011 — Dynamic schema introspection via information_schema
Date: 2026-06-30
Context: The LLM needs accurate, current knowledge of the database schema to generate correct SQL
Decision: Query PostgreSQL's `information_schema.columns` and `information_schema.table_constraints` at runtime rather than hardcoding the schema
Alternatives considered: Hardcoded Python dict of table/column names
Tradeoffs: Slightly more code upfront, but the schema injector auto-updates if tables or columns ever change — no manual sync required
Interview talking point: "The system introspects the live schema rather than relying on a stale hardcoded copy — if I add a column tomorrow, the LLM sees it automatically."

### D012 — CREATE TABLE-style DDL as schema format for the LLM
Date: 2026-06-30
Context: Needed to decide how to represent the schema in the prompt sent to the LLM
Decision: Format schema as realistic `CREATE TABLE` DDL statements rather than a custom compact notation
Alternatives considered: Lightweight custom format like `table(col: type, ...)`
Tradeoffs: More verbose, slightly more tokens per request, but LLMs are heavily trained on real SQL DDL and produce more accurate queries when the schema resembles familiar syntax
Interview talking point: "I formatted the schema as real DDL because LLMs perform better against patterns they've seen extensively in training — a custom notation would have required the model to generalize in ways it's less reliable at."

### D013 — Added real foreign key constraints to the database
Date: 2026-06-30
Context: Day 1's data load only declared primary keys — no foreign key relationships were enforced at the database level, despite the relationships existing conceptually
Decision: Added 7 explicit `FOREIGN KEY` constraints via `ALTER TABLE`, enabling automated FK discovery through `information_schema`
Alternatives considered: Hardcoding the relationship map in Python instead of enforcing it in the database
Tradeoffs: Found and fixed 2 real data-quality issues in the process (two product categories — `pc_gamer` and a kitchen-appliances category — had no matching row in the translation table); required inserting 2 missing translation rows before the constraints would apply cleanly
Interview talking point: "Adding real constraints surfaced two genuine data-quality issues in a well-known, supposedly clean dataset. I chose to fix the gap rather than hardcode around it, since enforced referential integrity is the more production-correct approach."

### D014 — SQL validation layer using sqlglot (STAR #1)
Date: 2026-06-30
Context: LLM-generated SQL can hallucinate table or column names that don't exist in the schema
Decision: Parse generated SQL with `sqlglot` and validate every referenced table and column against the real schema before execution; reject anything unrecognized
Alternatives considered: Regex-based string matching
Tradeoffs: Validates at table level strictly and column level more loosely (checking columns exist somewhere in the schema, not resolved to their exact source table) — a deliberate scope tradeoff to avoid building a full SQL semantic resolver
Interview talking point: "I used a proper SQL parser instead of regex because regex breaks on subqueries, aliases, and quoted identifiers — exactly the kind of edge case that would let bad SQL slip through silently."

### D015 — Restricted SQL generation to SELECT-only with row limits
Date: 2026-06-30
Context: LLM-generated SQL will eventually execute automatically against production data
Decision: System prompt enforces SELECT-only generation (no INSERT/UPDATE/DELETE/DROP/ALTER), with a default `LIMIT 20` unless the user requests a specific row count
Alternatives considered: Unrestricted generation with no row cap
Tradeoffs: None significant — protects against destructive queries and keeps token usage predictable on Groq's free tier
Interview talking point: "Since this SQL executes automatically with no human in the loop, restricting to read-only operations was a non-negotiable safety boundary, not an afterthought."

### D016 — Switched LLM model from Llama 3.1/3.3 70B to openai/gpt-oss-120b
Date: 2026-06-30
Context: Groq announced deprecation of `llama-3.3-70b-versatile` (and `llama-3.1-70b-versatile` was already deprecated in early 2025) on June 17, 2026
Decision: Use `openai/gpt-oss-120b`, Groq's recommended replacement model
Alternatives considered: Continuing with `llama-3.3-70b-versatile` until forced migration
Tradeoffs: Comparable quality and speed, avoids building the project on a model already flagged for removal
Interview talking point: "I checked Groq's current model documentation rather than assuming my original plan was still valid — the model I'd originally chosen had already been flagged for deprecation, so I migrated proactively instead of getting blocked mid-build."

### D017 — Sample categorical values injected into schema context
Date: 2026-06-30
Context: Testing revealed the LLM generated `customer_state = 'São Paulo'` instead of the correct stored value `'SP'`, since DDL alone shows column names and types but never actual data values
Decision: Centralized `CATEGORICAL_COLUMNS` list identifies known categorical columns (state, city, status, payment type, product category); their distinct sample values are queried and appended as inline comments in the generated DDL
Alternatives considered: Leaving the issue unaddressed as a documented limitation
Tradeoffs: Adds a small number of extra queries when building schema context, and slightly increases prompt token count, but directly fixes a real-world failure mode users would hit constantly (e.g. asking about "São Paulo" rather than "SP")
Interview talking point: "Testing surfaced a real semantic gap — the schema told the model column names but not column *values*. I fixed it at the root, in the schema injector, with one centralized function, rather than patching individual queries."

### D018 — Clarifying column notes for ambiguous schema semantics
Date: 2026-06-30
Context: Testing revealed the LLM defaulted to grouping by `customer_id` instead of `customer_unique_id` when answering "which customers placed more than 3 orders" — Olist's dataset uses `customer_id` as a per-order identifier and `customer_unique_id` as the true per-person identifier, a distinction invisible from column names and types alone
Decision: Added a `COLUMN_NOTES` dict alongside `CATEGORICAL_COLUMNS`, injecting clarifying inline comments into the DDL for semantically ambiguous columns (e.g. "unique per order, NOT per person")
Alternatives considered: Leaving the ambiguity undocumented and accepting incorrect SQL on customer-uniqueness questions
Tradeoffs: Comments reduce but do not reliably eliminate the failure rate — across 2 independent test runs with identical schema context, the model defaulted to `customer_id` both times rather than `customer_unique_id`, despite the clarifying comment. This suggests the comment's influence is weak rather than the failure being random variance, and that a stronger directive prompt rule (rather than a descriptive comment) would likely be needed for reliable correction.
Interview talking point: "I found a subtle data semantics issue specific to this dataset — two ID columns that look interchangeable but aren't — and documented it directly in the schema context the LLM sees. It also taught me a real limitation: LLM steering reduces error rates, it doesn't guarantee determinism."

### D019 — Hardened SQL validation against CTE false positives
Date: 2026-06-30
Context: After adding a system prompt rule directing the LLM to use CTEs for complex window-function queries (to fix a Postgres GROUP BY error on day-over-day calculations), the validation layer began rejecting valid queries — `sqlglot` correctly identified CTE names (e.g. `daily_counts`) as table references, but the validator had no way to distinguish a query-local CTE alias from an actual hallucinated table
Decision: Extended `validate_sql()` to collect all `exp.CTE` alias names from the parsed query and exclude them from the "unknown table" check, mirroring the existing pattern used for column aliases
Alternatives considered: Removing the CTE-encouraging prompt rule instead of fixing the validator
Tradeoffs: None significant — this is the correct fix, since CTEs are a standard, valid SQL construct and the validator's job is to catch genuine hallucinations, not reject correct SQL using legitimate features
Interview talking point: "Hardening the validation layer wasn't a single pass — first I found alias false positives, then CTE false positives, both surfaced through real testing rather than upfront assumptions. That iterative discovery process is exactly what I'd expect in a real production system."

### D020 — Sync route handlers over async, despite async-native driver choice
Date: 2026-07-01
Context: psycopg3 was chosen in D010 specifically for native async support, and FastAPI supports async route handlers natively
Decision: Day 3 endpoints (/health, /query, /history) use plain `def`, not `async def`
Alternatives considered: Making all routes async to match the driver's capability
Tradeoffs: Day 2's core functions (answer_question, execute_query, get_connection) are all synchronous. Mixing async route handlers with blocking sync calls inside them would block FastAPI's event loop, actively hurting performance rather than helping — the opposite of the intended benefit. Plain `def` routes run in FastAPI's thread pool automatically, which is safe with sync code.
Interview talking point: "I deliberately kept routes synchronous even though the driver supports async, because half-async — async routes calling blocking code — is worse than fully sync. Async only pays off when the whole chain underneath is also async, which wasn't true yet for the Day 2 pipeline."

### D021 — Redis cache key normalization (lowercase + whitespace collapse)
Date: 2026-07-01
Context: MD5-hashing the raw NL question string means trivial formatting differences (case, extra whitespace) produce different cache keys for what's effectively the same question
Decision: Normalize the question (lowercase, collapse whitespace) before hashing, applied identically on both read and write paths
Alternatives considered: Hash the raw string as-is; full semantic similarity matching via embeddings
Tradeoffs: Catches formatting-level duplicates cheaply (near-zero cost, no new dependencies) but does not catch semantically equivalent rephrasings using different wording (e.g. "average value" vs "average order value") — see Known Limitations
Interview talking point: "I caught a real gap during testing — identical questions with different casing or spacing were being treated as cache misses. Fixed it at the normalization step rather than the hashing step, since hashing can't be 'fuzzy' by design."

### D022 — Query log rotation via DELETE...NOT IN, capped at 100 rows
Date: 2026-07-01
Context: An unbounded query_log table would grow indefinitely with every request
Decision: After every insert, delete all rows except the 100 most recent (by created_at), using `DELETE FROM query_log WHERE id NOT IN (SELECT id ... ORDER BY created_at DESC LIMIT 100)`
Alternatives considered: Let the table grow unbounded and only limit reads in /history (simpler code, but doesn't actually solve unbounded growth — just hides it from the API)
Tradeoffs: One extra DELETE per request, negligible cost at this scale; guarantees the table never exceeds 100 rows at rest, not just at read time
Interview talking point: "I chose to actually enforce the cap at write time rather than fake it at read time — the second approach is simpler but doesn't solve the real problem, it just hides it behind the API."

### D023 — Redis-based rate limiting over in-memory counters
Date: 2026-07-01
Context: Needed to enforce 20 requests/minute per client
Decision: Redis fixed-window counter per client IP (`ratelimit:<ip>`), using INCR + EXPIRE (set only on the first request in a window)
Alternatives considered: In-memory Python dict/counter
Tradeoffs: In-memory counters reset on every server restart and don't work correctly across multiple server instances (e.g. behind a load balancer) — each instance would track its own separate count, making the limit meaningless. Redis is shared and already running, with TTL support built in.
Interview talking point: "I used Redis for rate limiting instead of an in-memory counter because rate limits need to be consistent across restarts and across multiple instances in production — an in-memory counter would silently break the moment you scale past one server."

### D024 — Known limitation: client IP resolution behind a proxy
Date: 2026-07-01
Context: Rate limiting keys on `request.client.host`, the raw connection IP
Decision: Accepted as-is for now; not fixed in Day 3
Tradeoffs: This works correctly for local testing and direct connections, but once deployed behind a reverse proxy or load balancer (e.g. Railway in Day 7), the raw connection IP often reflects the proxy, not the real client — every user could appear as the same IP, making rate limiting ineffective. The standard fix is reading a forwarded-IP header (e.g. X-Forwarded-For) instead, but that header can be spoofed unless the proxy is trusted and configured to overwrite it.
Interview talking point: "I flagged this rather than fixing it blind — trusting X-Forwarded-For without knowing exactly how Railway's proxy is configured could introduce a spoofing vector. This is something to verify against Railway's actual proxy behavior during Day 7 deployment, not guess at now."

### D025 — Leakage-safe feature selection for delay classifier

Only features knowable at order-purchase time were used (timestamps, geography, product dimensions/weight, price/freight, item/seller counts). Explicitly excluded: `order_delivered_carrier_date` and `order_delivered_customer_date` (the latter defines the label itself), and all of `order_reviews` (post-delivery, often caused by the delay itself — using it would be backwards causality). Seller historical late-rate was considered but deferred — see Post-Completion Improvements.

### D026 — Class imbalance handled via scale_pos_weight, not resampling

With an 8.11% positive rate, `scale_pos_weight` (computed as negative/positive ratio on the training split only, ≈11.3) was used instead of SMOTE or other resampling. Simpler pipeline, no synthetic data to justify, and sufficient given the modest but real lift achieved (PR-AUC 0.288 vs ~0.081 baseline, ~3.5x). Classification threshold was tuned via F1-maximization on the precision-recall curve (landed at 0.707) rather than left at the default 0.5, since that's the threshold actually shipped to `/predict`.

### D027 — predict_proba over predict, with separate UI-badge buckets

The `/predict` endpoint returns a continuous risk score (`predict_proba`) rather than a hard label, so downstream UI (Day 6 badges) can distinguish "barely risky" from "very likely late." Two separate thresholds are used deliberately: 0.707 (F1-optimal) for `is_late_predicted`, and looser placeholder cutoffs (0.3/0.6) for the green/amber/red badge — the badge is a softer "worth a second look" signal, not a restatement of the classification decision.

### D028 — /predict scoped to single-order queries, no delivery-status filter

Initial design pulled and rebuilt features for all ~96k orders on every `/predict` call — fixed same-day after recognizing it both violated the <80ms latency target (STAR #3) and was conceptually wrong: predicting delay only makes sense for orders that haven't been delivered yet, so no status filter is applied. Single-order query functions (`load_single_order_raw`, `load_single_order_items_agg`) and a shared `_add_derived_features()` helper were added so training and inference feature logic can't silently diverge.

### D029 — Next.js 16 instead of originally planned Next.js 14**
`create-next-app@latest` installed Next.js 16.2.10 and Tailwind v4 at time of scaffolding (June/July 2026), not the version assumed when the stack table was first written. Tailwind v4 drops the separate `tailwind.config.ts` file in favor of CSS-based config via `@import "tailwindcss"` in `globals.css`. No functional impact — noted so the stack table and actual repo don't silently diverge.

### D030 — CORS scoped to explicit origin, not wildcard**
`backend/main.py` allows only `http://localhost:3000` via `CORSMiddleware`, rather than `allow_origins=["*"]`. Deliberate tight scoping — the frontend and backend are a known pair, and wildcard CORS is the kind of default that looks fine in a demo and wrong in a security review.

### D031 — Columns derived from result keys, not a separate backend field**
`QueryResponse` (see `backend/models.py`) returns `results: list[dict]` with no separate `columns` list. Frontend derives table headers via `Object.keys(results[0])` instead of requiring the backend to send redundant column metadata. Keeps the response payload minimal; revisit only if column order ever needs to be guaranteed independent of dict key order (Python 3.7+ dicts preserve insertion order, so not currently a risk).

### D032 — Skipped shadcn/ui, hand-built components with Tailwind directly**
The original stack table listed shadcn/ui for "polished UI without deep frontend knowledge." In practice, the custom dark theme (deep indigo palette, 3D hero pipeline, glass-morphic cards) needed enough visual control that shadcn's default component styles would have required overriding rather than saving effort. Chat input, button, and results table were hand-built with raw Tailwind utility classes instead. Known deviation from the original stack decision, logged rather than left silently inconsistent.

### D033 — Live health-check status pill instead of a static "Live" label**
The nav bar's status indicator calls `GET /health` on page load and reflects the real response (green/red dot) rather than displaying a hardcoded "Live" badge. Small decision, but the difference between a UI element that's honest about backend state versus one that's purely decorative.

---

## Data Insights

### Olist Dataset — Key findings from Day 1 exploration

- Dataset covers 2017–2018, approximately 2 years of real Brazilian e-commerce data
- 99,441 total orders across 9 tables
- 97% of orders are delivered (96,478) — only 3% in other states
- 625 cancelled orders — exclude from delivery time calculations
- Credit card is dominant payment method (74% of payments, avg R$163.32)
- São Paulo accounts for 42% of all orders — largest market by far
- Health & beauty is top revenue category at R$1.25M
- Most orders delivered significantly early — Olist builds buffer into estimates
- 8.11% late delivery rate — confirmed class imbalance (7,826 late vs 88,644 on time)
- ML model needs scale_pos_weight to handle class imbalance
- F1 score and precision/recall are primary metrics, not accuracy
- 7,826 late orders — sufficient minority class for training
- Late deliveries correlate with lower review scores (seen in seller analysis)
- Top revenue seller has 11.49% late rate — above platform average of 8.11%

### Day 2 additional finding
- Found 2 data-quality gaps in product_category_name_translation: missing translations 
  for `pc_gamer` (3 products) and `portateis_cozinha_e_preparadores_de_alimentos`. 
  Fixed by inserting translation rows rather than altering product data.

---

## SQL Patterns Learned

### Patterns to reuse in Text-to-SQL engine

- DATE_TRUNC('month', timestamp) — group by month
- EXTRACT(DOW FROM timestamp) — day of week (0=Sunday)
- EXTRACT(MONTH FROM timestamp) — month number
- SUM(CASE WHEN condition THEN 1 ELSE 0 END) — conditional count
- COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() — percentage with window function
- Multiple JOINs chained — orders → order_items → products → category_translation
- IS NOT NULL — always filter nulls on delivery date columns
- ROUND(value, 2) — always round money values
- COUNT(DISTINCT column) — avoid double counting in JOINs

---

## Known Limitations (as of end of Day 2)

### LLM non-determinism on customer identity questions
Questions involving "customers" sometimes use `customer_id` (per-order identifier) instead of 
the correct `customer_unique_id` (per-person identifier), despite a clarifying schema comment. 
Confirmed across 2 independent test runs with identical context — both defaulted incorrectly. 
A descriptive comment alone is insufficient; a stronger directive prompt rule would likely be 
needed to fix this reliably. Deferred — not core to Day 2 scope, revisit if it surfaces again 
during Day 3+ testing.

### Complex window-function queries occasionally produce invalid SQL on first attempt
One test question (day-over-day percentage change using LAG over grouped data) initially failed 
with a Postgres GROUP BY error. Fixed via a combination of (1) an explicit system prompt rule 
directing the LLM to use CTEs for this pattern, and (2) hardening the validation layer to not 
flag CTE aliases as hallucinated tables. Resolved and verified working as of end of Day 2.

### Validation layer scope
`validate_sql()` checks that every referenced table exists in the schema (strict) and that every 
referenced column exists *somewhere* in the schema (loose — not resolved to its specific source 
table). This was a deliberate scope decision to avoid building a full SQL semantic resolver. 
It will not catch a column being referenced against the wrong table if both the column name and 
the table name are independently valid elsewhere in the schema.

### Cache matching is exact (normalized), not semantic
The Redis cache (D021) catches formatting differences (case, whitespace) but treats 
differently-worded questions with the same meaning (e.g. "average value" vs "average order 
value") as distinct cache entries. A true fix requires embedding-based similarity matching 
(e.g. sentence-transformers + cosine similarity), backed by a vector-search-capable store 
(pgvector, or Redis with a vector module). This is a meaningfully larger scope than string-level 
caching and was deliberately deferred rather than attempted mid-Day-3. Flagged as a strong 
candidate for a post-completion improvement.

### Model performance ceiling (Day 4)
Current PR-AUC (0.288) and F1 (0.36 at tuned threshold) are a real but modest lift over baseline. The single biggest known lever left unused is seller historical late-rate, deliberately deferred due to the time-aware aggregation required to compute it without leakage (must only use orders prior to the current order's timestamp). Revisit as a dedicated pass once Days 5–8 are complete, or as a documented future-work item if time runs out.

### Risk badge cutoffs are placeholders (Day 4)
The 0.3/0.6 green/amber/red boundaries were set without inspecting the real probability distribution on the test set. Revisit once more predictions have been observed, ideally against `metrics.json`'s score distribution.

### Hardcoded local API URL (Day 5)

`frontend/.env.local` currently sets `NEXT_PUBLIC_API_URL=http://localhost:8000`, which only works for local dev. Once the backend is deployed to Railway (Day 7), this needs to be updated to the live Railway URL — either via Vercel's environment variable settings (not `.env.local`, which won't be committed or deployed) or a separate `.env.production` file. Flagging now so it's not a last-minute surprise during deployment when the frontend silently fails to reach the API.