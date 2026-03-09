from sentence_transformers import SentenceTransformer
import chromadb

EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="rag_docs")


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Embed the query, search Chroma for the most relevant chunks,
    return a list of {text, source, page} dicts.
    """
    # 1. Embed the user query with the same model used at ingestion
    query_embedding = EMBEDDING_MODEL.encode(query).tolist()

    # 2. Search the vector DB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # 3. Package results cleanly
    chunks = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": text,
            "source": metadata.get("source", "unknown"),
            "page": metadata.get("page", 0),
            "relevance_score": round(1 - distance, 4)  # convert distance → similarity
        })

    return chunks