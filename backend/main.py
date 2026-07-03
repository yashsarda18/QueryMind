import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from fastapi import FastAPI, Request, HTTPException
from models import QueryRequest, QueryResponse, HistoryEntry
from sql_engine import answer_question
from database import get_connection, log_query, get_history
from cache import get_cached_result, set_cached_result, check_rate_limit
from ml_model import get_model
from ml.features import load_single_order_raw, load_single_order_items_agg, build_inference_features
from models import PredictRequest, PredictResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title = "QueryMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, http_request: Request):
    client_id = http_request.client.host

    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 20 requests per minute.")
    cached = get_cached_result(request.question)
    if cached is not None:
        log_query(request.question, cached.get("sql"), cached["status"])
        return cached
    
    result = answer_question(request.question)
    if result["status"] == "success":
        set_cached_result(request.question, result)
    
    log_query(request.question, result.get("sql"), result["status"])
    return result

@app.get("/history", response_model=list[HistoryEntry])
def history(limit: int = 20):
    return get_history(limit)

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    conn = get_connection()
    order_row = load_single_order_raw(conn, request.order_id)
    items_agg_row = load_single_order_items_agg(conn, request.order_id)
    conn.close()

    if order_row.empty or items_agg_row.empty:
        raise HTTPException(status_code=404, detail="order_id not found")

    features = build_inference_features(order_row, items_agg_row)
    if features is None:
        raise HTTPException(status_code=404, detail="order_id not found")

    model = get_model()
    result = model.predict(features)

    return {"order_id": request.order_id, **result}
    