import os
import pdfplumber
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()

EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="rag_docs")


def load_pdf_with_pdfplumber(pdf_path: str) -> list[Document]:
    """Extract text from each page using pdfplumber — handles printed/browser PDFs well."""
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


def ingest_pdf(pdf_path: str):
    """Load a PDF, chunk it, embed it, store in Chroma."""
    print(f"📄 Loading: {pdf_path}")

    # 1. Load PDF pages
    pages = load_pdf_with_pdfplumber(pdf_path)

    if not pages:
        print(f"⚠️  No text could be extracted from {pdf_path}. Skipping.")
        return

    print(f"📖 Extracted text from {len(pages)} page(s)")

    # 2. Split into overlapping chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(pages)
    print(f"✂️  Split into {len(chunks)} chunks")

    if not chunks:
        print("⚠️  Chunking produced no results. Skipping.")
        return

    # 3. Embed each chunk
    texts = [chunk.page_content for chunk in chunks]
    embeddings = EMBEDDING_MODEL.encode(texts).tolist()

    # 4. Store in Chroma with metadata
    ids = [f"{Path(pdf_path).stem}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": pdf_path,
            "page": chunk.metadata.get("page", 0),
            "chunk_index": i
        }
        for i, chunk in enumerate(chunks)
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"✅ Ingested {len(chunks)} chunks from {Path(pdf_path).name}\n")


def ingest_all_pdfs(docs_folder: str = "./docs"):
    """Ingest every PDF in the docs folder."""
    pdf_files = list(Path(docs_folder).glob("*.pdf"))

    if not pdf_files:
        print("⚠️  No PDFs found in ./docs — add some PDFs and try again.")
        return

    for pdf_path in pdf_files:
        ingest_pdf(str(pdf_path))

    print(f"🎉 Done! {len(pdf_files)} PDF(s) ingested into Chroma.")