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