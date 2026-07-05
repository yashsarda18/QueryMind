from pydantic import BaseModel
from typing import List, Optional, Literal, Any
from datetime import datetime

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    status: Literal["success", "unanswerable", "invalid_sql", "execution_error"]
    message: Optional[str] = None
    sql: Optional[str] = None
    results: Optional[list[dict[str, Any]]] = None
    
class HistoryEntry(BaseModel):
    id: int
    question: str
    sql: Optional[str] = None
    status: str
    created_at: datetime

class PredictRequest(BaseModel):
    order_id: str

class PredictResponse(BaseModel):
    order_id: str
    risk_score: float
    is_late_predicted: bool
    risk_badge: str

class BatchPredictRequest(BaseModel):
    order_ids: List[str]
    
class BatchPredictResult(BaseModel):
    order_id: str
    risk_score: Optional[float] = None
    is_late_predicted: Optional[bool] = None
    risk_badge: Optional[str] = None
    error: Optional[str] = None
    
class BatchPredictResponse(BaseModel):
    results: List[BatchPredictResult]