import os
import anthropic
from dotenv import load_dotenv
from ingestor import ingest_all_pdfs
from retriever import retrieve

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Assemble the context + question into a structured prompt."""
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


def ask(query: str):
    """Full RAG pipeline: retrieve → build prompt → call Claude → print answer."""
    print(f"\n🔍 Query: {query}")
    print("-" * 60)

    # 1. Retrieve relevant chunks
    chunks = retrieve(query, top_k=5)

    if not chunks:
        print("⚠️  No relevant chunks found. Have you ingested any documents?")
        return

    print(f"📚 Retrieved {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  [{i+1}] Score: {chunk['relevance_score']} | "
              f"{chunk['source']} p.{chunk['page']}")

    # 2. Build the prompt
    prompt = build_prompt(query, chunks)

    # 3. Call Claude
    print("\n🤖 Claude's Answer:")
    print("-" * 60)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    print(message.content[0].text)


if __name__ == "__main__":
    # Step 1: Ingest all PDFs in the ./docs folder
    print("=== INGESTION PHASE ===")
    ingest_all_pdfs("./docs")

    # Step 2: Ask questions
    print("\n=== QUERY PHASE ===")
    ask("What is this document about?")
    ask("What are the main topics covered?")