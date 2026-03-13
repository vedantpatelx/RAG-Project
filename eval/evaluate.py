import json
import time
import requests
import statistics

API_URL = "http://54.145.246.203:8000"

# Test questions with expected keywords that should appear in retrieved chunks
TEST_CASES = [
    {
        "question": "What is the attention mechanism in transformers?",
        "expected_keywords": ["attention", "query", "key", "value"]
    },
    {
        "question": "What is multi-head attention?",
        "expected_keywords": ["multi-head", "heads", "parallel"]
    },
    {
        "question": "How do transformers handle positional encoding?",
        "expected_keywords": ["positional", "encoding", "position"]
    },
    {
        "question": "What is the encoder decoder structure?",
        "expected_keywords": ["encoder", "decoder", "stack"]
    },
    {
        "question": "What optimizer was used to train the transformer?",
        "expected_keywords": ["adam", "optimizer", "learning rate"]
    }
]


def evaluate():
    results = []
    print("=" * 60)
    print("RAG EVALUATION REPORT")
    print("=" * 60)

    for i, test in enumerate(TEST_CASES):
        question = test["question"]
        keywords = test["expected_keywords"]

        start = time.time()
        try:
            response = requests.post(
                f"{API_URL}/query",
                json={"question": question, "top_k": 3},
                timeout=30
            )
            latency = time.time() - start

            if response.status_code != 200:
                print(f"\n[{i+1}] FAILED: {question}")
                print(f"     Status: {response.status_code}")
                continue

            data = response.json()
            sources = data.get("sources", [])

            # Metric 1: Average rerank score
            rerank_scores = [s.get("rerank_score", 0) for s in sources if s.get("rerank_score")]
            avg_rerank = statistics.mean(rerank_scores) if rerank_scores else 0

            # Metric 2: Keyword hit rate
            all_text = " ".join([s["text"].lower() for s in sources])
            hits = sum(1 for kw in keywords if kw.lower() in all_text)
            keyword_hit_rate = hits / len(keywords)

            # Metric 3: Top chunk rerank score
            top_score = max(rerank_scores) if rerank_scores else 0

            results.append({
                "question": question,
                "avg_rerank_score": avg_rerank,
                "top_rerank_score": top_score,
                "keyword_hit_rate": keyword_hit_rate,
                "latency_seconds": latency,
                "num_sources": len(sources)
            })

            print(f"\n[{i+1}] {question}")
            print(f"     Avg Rerank Score : {avg_rerank:.4f}")
            print(f"     Top Rerank Score : {top_score:.4f}")
            print(f"     Keyword Hit Rate : {keyword_hit_rate:.0%} ({hits}/{len(keywords)} keywords found)")
            print(f"     Latency          : {latency:.2f}s")
            print(f"     Sources returned : {len(sources)}")

        except Exception as e:
            print(f"\n[{i+1}] ERROR: {question}")
            print(f"     {str(e)}")

        time.sleep(2)

    if results:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Questions tested    : {len(results)}/{len(TEST_CASES)}")
        print(f"Avg rerank score    : {statistics.mean([r['avg_rerank_score'] for r in results]):.4f}")
        print(f"Avg keyword hit rate: {statistics.mean([r['keyword_hit_rate'] for r in results]):.0%}")
        print(f"Avg latency         : {statistics.mean([r['latency_seconds'] for r in results]):.2f}s")

        # Save results to JSON
        with open("eval/results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to eval/results.json")


if __name__ == "__main__":
    evaluate()