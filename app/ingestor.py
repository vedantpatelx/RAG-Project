import os
import hashlib
import pdfplumber
import boto3
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

load_dotenv()

# Embedding model — must match retriever
from embedder import embed_batch

# AWS S3
s3_client = boto3.client("s3")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

# Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))


def upload_to_s3(local_path: str, filename: str) -> str:
    """Upload a file to S3 and return the S3 URI."""
    s3_key = f"documents/{filename}"
    s3_client.upload_file(local_path, S3_BUCKET, s3_key)
    s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
    print(f"☁️  Uploaded to S3: {s3_uri}")
    return s3_uri


def load_pdf_with_pdfplumber(pdf_path: str) -> list[Document]:
    """Extract text from each page using pdfplumber."""
    documents = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():  # skip blank pages
                documents.append(Document(
                    page_content=text.strip(),
                    metadata={"source": pdf_path, "page": page_num}
                ))
    return documents


def is_valid_chunk(text: str) -> bool:
    """Filter out garbled, mirrored, or low-quality chunks."""
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
    """
    Generate a stable unique ID for each chunk using a hash.
    This ensures we never duplicate vectors in Pinecone on re-ingestion.
    """
    content = f"{filename}_{chunk_index}_{text[:100]}"
    return hashlib.md5(content.encode()).hexdigest()


def ingest_pdf(pdf_path: str):
    """Load a PDF, upload to S3, chunk it, embed it, store in Pinecone."""
    filename = Path(pdf_path).name
    print(f"📄 Loading: {filename}")

    # 1. Upload raw file to S3 first
    s3_uri = upload_to_s3(pdf_path, filename)

    # 2. Extract text
    pages = load_pdf_with_pdfplumber(pdf_path)
    if not pages:
        print(f"⚠️  No text extracted from {filename}. Skipping.")
        return

    print(f"📖 Extracted text from {len(pages)} page(s)")

    # 3. Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(pages)

    # 4. Filter garbage
    valid_chunks = [c for c in chunks if is_valid_chunk(c.page_content)]
    skipped = len(chunks) - len(valid_chunks)
    if skipped > 0:
        print(f"🗑️  Filtered out {skipped} garbage chunks")
    chunks = valid_chunks

    if not chunks:
        print("⚠️  No valid chunks after filtering. Skipping.")
        return

    print(f"✂️  {len(chunks)} clean chunks to embed")

    # 5. Embed + upsert to Pinecone in batches of 100
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embed_batch(texts)

    batch_size = 100
    upserted = 0

    for i in range(0, len(chunks), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        batch_chunks = chunks[i:i + batch_size]

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
                    "source": s3_uri,      # S3 URI instead of local path
                    "filename": filename,
                    "page": chunk.metadata.get("page", 0),
                    "chunk_index": i + j
                }
            })

        index.upsert(vectors=vectors)
        upserted += len(vectors)
        print(f"  ⬆️  Upserted batch {i // batch_size + 1} ({upserted}/{len(chunks)})")

    print(f"✅ Ingested {upserted} chunks from {filename} into Pinecone\n")


def ingest_all_pdfs(docs_folder: str = "./docs"):
    """Ingest every PDF in the docs folder."""
    pdf_files = list(Path(docs_folder).glob("*.pdf"))

    if not pdf_files:
        print("⚠️  No PDFs found in ./docs")
        return

    for pdf_path in pdf_files:
        ingest_pdf(str(pdf_path))

    print(f"🎉 Done! {len(pdf_files)} PDF(s) ingested.")