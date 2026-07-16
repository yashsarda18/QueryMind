# QueryMind

QueryMind is a full-stack analytics and prediction platform built around e-commerce order intelligence. It combines a Next.js front-end with a FastAPI back-end, a PostgreSQL analytics database, Redis caching, and an XGBoost-based delivery delay risk model.

## Overview

The application is designed to let users:

- Ask natural-language questions about the dataset and receive validated SQL-backed answers.
- Inspect generated SQL for transparency.
- Evaluate delivery risk for one or more orders using a live batch prediction endpoint.

The pipeline is intentionally end-to-end:

- A language model converts business questions into SQL.
- SQL is validated against the actual Postgres schema.
- Results are executed on a real dataset derived from the Olist e-commerce dataset.
- A batch inference API provides delivery delay risk predictions for order IDs.

## Architecture

- `frontend/` — Next.js 16 application with React 19, Tailwind CSS, and a production-ready SPA interface.
- `backend/` — FastAPI service exposing query, prediction, and health endpoints.
- `data/` — SQL schema, foreign-key wiring, and data loading scripts for Postgres.
- `ml/` — Model training and inference utilities using XGBoost.
- `docker-compose.yml` — local Postgres and Redis service definitions.

## Key Features

- Natural language to SQL translation using Groq/OpenAI-style generative prompts.
- SQL validation against a real Postgres schema using `sqlglot`.
- Postgres-backed query execution with safe `SELECT`-only rules and capped result rows.
- Redis-based caching and rate limiting for query endpoints.
- Delivery delay risk prediction with batch support (`/predict/batch`) and frontend UI integration.
- Structured `BatchPredictResult` responses including risk score, late prediction flag, and badge.

## Repo Structure

```
backend/             # FastAPI service, database access, caching, and prediction logic
frontend/            # Next.js UI and risk predictor interface
ml/                  # Model training, feature engineering, and saved artifacts
data/                # Postgres data load scripts and dataset CSV files
docker-compose.yml   # Local Postgres and Redis service composition
.env.example         # Required environment variables for local setup
README.md            # Project overview and setup instructions
```

## Backend Details

The backend exposes the following endpoints:

- `GET /health` — health check for Postgres connectivity.
- `POST /query` — accepts `{ question: string }`, returns validated SQL and query results.
- `GET /history` — returns the most recent query log entries.
- `POST /predict` — single order delivery risk prediction.
- `POST /predict/batch` — batch order delivery risk prediction (limited to 25 order IDs).

Important backend behaviors:

- Rate limit: 20 requests per minute per client IP.
- Query caching in Redis to avoid repeated LLM SQL generation for the same question.
- Batch prediction returns an error-per-row model result instead of failing the whole request.
- The ML model is lazily loaded from `ml/model.joblib` and `ml/encoders.joblib`.

## Frontend Details

The frontend is a modern Next.js 16 application with:

- A live query UI for natural-language SQL queries.
- A delivery risk predictor panel for batch order ID scoring.
- Consistent dark theme, accent styling, and responsive layout.
- Example order IDs preloaded for fast testing.

The frontend uses `NEXT_PUBLIC_API_URL` to target the backend, and the sample local config expects the API on `http://localhost:8000`.

## Model Training

The model pipeline is implemented in `ml/train.py`:

- Extracts training data from Postgres via `ml/features.py`.
- Encodes categorical features and handles unseen categories safely.
- Trains an XGBoost classifier with a tuned threshold for late delivery prediction.
- Saves `model.joblib`, `encoders.joblib`, and `metrics.json` for inference.

## Local Setup

### Prerequisites

- Python 3.13+
- Node.js 20+
- PostgreSQL database
- Redis instance
- `pip` and `npm`

### Environment

Copy the example env file and populate the values:

```bash
cp .env.example .env
```

### Backend

```bash
python -m venv .venv
.venv/Scripts/activate    # Windows
# or
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database & Data Loading

The project includes SQL scripts for schema setup and data ingestion under `data/`.

A typical workflow is:

1. Start Postgres and Redis locally using `docker compose up -d`.
2. Create the database and user matching `.env` values.
3. Load the schema and data:
   ```bash
   - `\i load_olist.sql`
   - `\i add_foreign_keys.sql`
   - `\i load_data.sql`
   ```
### Example local frontend config

`frontend/.env.local` should contain:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment Notes

- The backend is deployed on AWS and can be containerized using `backend/Dockerfile`.
- The frontend is deployed on Vercel and consumes the backend via `NEXT_PUBLIC_API_URL`.
- `docker-compose.yml` is provided for local Postgres and Redis development only.
- Production deployments should configure secrets through environment variables and avoid committing local `.env` files.

## Technical Highlights

- Language-model-driven SQL generation with schema-aware system prompts.
- SQL validation using `sqlglot` before execution.
- XGBoost inference with categorical encoding and risk bucketing.
- Batch-safe prediction API with graceful per-order error handling.
- Modern UI built with Next.js, React, Tailwind CSS, and reusable component architecture.

## Notes for Reviewers

- The backend is intentionally separated from the frontend, which allows independent scaling.
- The ML inference path is stateless once models are loaded, making it suitable for containerized deployment.
- The query translation layer emphasizes transparency by exposing generated SQL and validation feedback.
- The current implementation uses Groq for LLM-driven SQL generation; the prompt is tightly coupled to the actual database schema.

If you want, I can also add a concise `CONTRIBUTING.md` or a high-level `ARCHITECTURE.md` for this repo.
