from pydantic import BaseModel
from typing import Optional, Literal, Any
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

