from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class ChunkResult(BaseModel):
    text: str
    source: str
    page: int
    relevance_score: float


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