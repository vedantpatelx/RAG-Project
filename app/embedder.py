from sentence_transformers import SentenceTransformer

# Load once, shared across ingestor and retriever
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> list[float]:
    return EMBEDDING_MODEL.encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return EMBEDDING_MODEL.encode(texts).tolist()