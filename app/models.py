from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class ChunkResult(BaseModel):
    text: str
    source: str
    page: int
    score: Optional[float] = None
    rerank_score: Optional[float] = None
    filename: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[ChunkResult]


class IngestResponse(BaseModel):
    filename: str
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    message: str