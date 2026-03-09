import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

load_dotenv()

from embedder import embed_text

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Embed the query, search Pinecone for the most relevant chunks,
    return a list of {text, source, page, relevance_score} dicts.
    """
    # 1. Embed the query
    query_embedding = embed_text(query)

    # 2. Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    # 3. Package results
    chunks = []
    for match in results["matches"]:
        chunks.append({
            "text": match["metadata"].get("text", ""),
            "source": match["metadata"].get("source", "unknown"),
            "page": match["metadata"].get("page", 0),
            "relevance_score": round(match["score"], 4)
        })

    return chunks