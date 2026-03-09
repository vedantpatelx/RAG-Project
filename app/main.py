import os
import shutil
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ingestor import ingest_pdf
from retriever import retrieve
from models import QueryRequest, QueryResponse, ChunkResult, IngestResponse, HealthResponse

load_dotenv()

# ── App setup ──────────────────────────────────────────────
app = FastAPI(
    title="RAG API",
    description="A production-grade Retrieval-Augmented Generation API powered by Claude.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

UPLOAD_DIR = Path("../docs")
UPLOAD_DIR.mkdir(exist_ok=True)


# ── Prompt builder ─────────────────────────────────────────
def build_prompt(query: str, chunks: list[dict]) -> str:
    context_blocks = []
    for i, chunk in enumerate(chunks):
        context_blocks.append(
            f"[Source {i+1}: {chunk['source']}, Page {chunk['page']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are a helpful assistant. Answer the user's question using ONLY the context provided below.
If the answer is not in the context, say "I don't have enough information to answer that."
Always cite which source(s) you used in your answer.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""


# ── Routes ─────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check that the API is running."""
    return HealthResponse(status="ok", message="RAG API is running.")


@app.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload a PDF and ingest it into the vector store.
    The file is saved to /docs and processed immediately.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save uploaded file to docs/
    save_path = UPLOAD_DIR / file.filename
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingest it
    try:
        ingest_pdf(str(save_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return IngestResponse(
        filename=file.filename,
        status="success",
        message=f"{file.filename} has been ingested into the vector store."
    )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Ask a question. Returns Claude's answer grounded in your ingested documents.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Retrieve relevant chunks
    chunks = retrieve(request.question, top_k=request.top_k)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found. Have you ingested any PDFs?"
        )

    # 2. Build prompt + call Claude
    try:
        prompt = build_prompt(request.question, chunks)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = message.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    # 3. Return structured response
    return QueryResponse(
        question=request.question,
        answer=answer,
        sources=[ChunkResult(**chunk) for chunk in chunks]
    )