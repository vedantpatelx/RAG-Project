import boto3
import json
from pinecone import Pinecone
from embedder import embed_text

bedrock_agent = boto3.client("bedrock-agent-runtime", region_name="us-east-1")


def rerank(query: str, chunks: list[dict], top_n: int) -> list[dict]:
    sources = [
        {
            "type": "INLINE",
            "inlineDocumentSource": {
                "type": "TEXT",
                "textDocument": {"text": chunk["text"]}
            }
        }
        for chunk in chunks
    ]

    response = bedrock_agent.rerank(
        rerankingConfiguration={
            "type": "BEDROCK_RERANKING_MODEL",
            "bedrockRerankingConfiguration": {
                "modelConfiguration": {
                    "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/cohere.rerank-v3-5:0"
                },
                "numberOfResults": top_n
            }
        },
        sources=sources,
        queries=[{"type": "TEXT", "textQuery": {"text": query}}]
    )

    reranked = []
    for result in response["results"]:
        chunk = chunks[result["index"]].copy()
        chunk["rerank_score"] = result["relevanceScore"]
        reranked.append(chunk)

    return reranked


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
    secret = secrets_client.get_secret_value(SecretId="rag-project/env")
    secrets = json.loads(secret["SecretString"])

    pc = Pinecone(api_key=secrets["PINECONE_API_KEY"])
    index = pc.Index(secrets["PINECONE_INDEX_NAME"])

    query_embedding = embed_text(query)

    results = index.query(
        vector=query_embedding,
        top_k=20,
        include_metadata=True
    )

    if not results["matches"]:
        return []

    chunks = [
        {
            "text": match["metadata"]["text"],
            "source": match["metadata"].get("source", ""),
            "filename": match["metadata"].get("filename", ""),
            "page": match["metadata"].get("page", 0),
            "score": match["score"]
        }
        for match in results["matches"]
    ]

    return rerank(query, chunks, top_n=top_k)