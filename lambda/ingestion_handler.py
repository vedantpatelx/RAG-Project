import os
import json
import hashlib
import tempfile
import boto3
import pdfplumber
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

# AWS clients — initialized once for warm start performance
s3_client = boto3.client("s3")
bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")


def get_secrets():
    """Fetch secrets from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret = client.get_secret_value(SecretId="rag-project/env")
    return json.loads(secret["SecretString"])


secrets = get_secrets()
pc = Pinecone(api_key=secrets["PINECONE_API_KEY"])
index = pc.Index(secrets["PINECONE_INDEX_NAME"])


def embed_text(text: str) -> list[float]:
    """Embed text using AWS Bedrock Titan."""
    response = bedrock_client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text})
    )
    return json.loads(response["body"].read())["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts — Titan doesn't support batch so we loop."""
    return [embed_text(text) for text in texts]


def load_pdf(local_path: str) -> list[Document]:
    """Extract text from PDF pages."""
    documents = []
    with pdfplumber.open(local_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                documents.append(Document(
                    page_content=text.strip(),
                    metadata={"page": page_num}
                ))
    return documents


def is_valid_chunk(text: str) -> bool:
    """Filter out garbled or low quality chunks."""
    if len(text.strip()) < 50:
        return False
    words = text.split()
    if len(words) < 10:
        return False
    single_chars = sum(1 for w in words if len(w) == 1 and w.isalpha())
    if single_chars / len(words) > 0.3:
        return False
    avg_word_len = sum(len(w) for w in words) / len(words)
    if avg_word_len < 2 or avg_word_len > 15:
        return False
    return True


def make_chunk_id(filename: str, chunk_index: int, text: str) -> str:
    """Generate a stable unique ID for each chunk."""
    content = f"{filename}_{chunk_index}_{text[:100]}"
    return hashlib.md5(content.encode()).hexdigest()


def process_pdf(bucket: str, key: str):
    """Download PDF from S3, chunk, embed, and store in Pinecone."""
    filename = Path(key).name
    print(f"📄 Processing: {filename} from s3://{bucket}/{key}")

    # 1. Download PDF from S3 to a temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        s3_client.download_file(bucket, key, tmp.name)
        local_path = tmp.name

    # 2. Extract text
    pages = load_pdf(local_path)
    if not pages:
        print(f"⚠️  No text extracted from {filename}")
        return {"status": "skipped", "reason": "no text extracted"}

    print(f"📖 Extracted {len(pages)} pages")

    # 3. Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(pages)

    # 4. Filter garbage
    valid_chunks = [c for c in chunks if is_valid_chunk(c.page_content)]
    print(f"✂️  {len(valid_chunks)} valid chunks after filtering")

    if not valid_chunks:
        return {"status": "skipped", "reason": "no valid chunks"}

    # 5. Embed using Bedrock Titan
    texts = [c.page_content for c in valid_chunks]
    embeddings = embed_batch(texts)

    # 6. Upsert to Pinecone in batches
    s3_uri = f"s3://{bucket}/{key}"
    batch_size = 100
    upserted = 0

    for i in range(0, len(valid_chunks), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        batch_chunks = valid_chunks[i:i + batch_size]

        vectors = []
        for j, (text, embedding, chunk) in enumerate(
            zip(batch_texts, batch_embeddings, batch_chunks)
        ):
            chunk_id = make_chunk_id(filename, i + j, text)
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "text": text,
                    "source": s3_uri,
                    "filename": filename,
                    "page": chunk.metadata.get("page", 0),
                    "chunk_index": i + j
                }
            })

        index.upsert(vectors=vectors)
        upserted += len(vectors)
        print(f"⬆️  Upserted {upserted}/{len(valid_chunks)} chunks")

    print(f"✅ Done! {upserted} chunks ingested from {filename}")
    return {"status": "success", "chunks_ingested": upserted, "filename": filename}


def handler(event, context):
    """Lambda entry point — triggered by S3 PUT events."""
    print(f"🔔 Event received: {json.dumps(event)}")

    results = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.lower().endswith(".pdf"):
            print(f"⏭️  Skipping non-PDF: {key}")
            continue

        result = process_pdf(bucket, key)
        results.append(result)

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }