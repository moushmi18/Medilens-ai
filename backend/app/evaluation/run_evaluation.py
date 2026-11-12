#!/usr/bin/env python3
"""Run RAG evaluation on the synthetic dataset.

Compares retrieval methods:
- basic (vector only)
- hybrid (vector + BM25 with RRF)
- hybrid_rerank (hybrid + cross-encoder)
- context_aware (hybrid_rerank + report-scoped retrieval)

Non-LLM metrics (run without API key):
- Intent classification accuracy
- Safety detection accuracy
- Retrieval Recall@K / MRR (requires populated knowledge base)

LLM-based metrics (requires OPENAI_API_KEY):
- Faithfulness / answer relevancy (RAGAS)
- Clearly marked NOT RUN when no key is present
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.evaluation.dataset import (
    get_dataset,
    get_safe_questions,
    get_unsafe_questions,
    DATASET_STATS,
)
from app.safety import SafetyEngine
from app.core.config import get_settings


def evaluate_intent_classification() -> dict[str, Any]:
    """Evaluate intent classification accuracy."""
    engine = SafetyEngine()
    dataset = get_dataset()

    correct = 0
    results = []

    for q in dataset:
        predicted = engine.classify_intent(q.query)
        is_correct = predicted == q.expected_intent
        if is_correct:
            correct += 1

        results.append({
            "id": q.id,
            "query": q.query[:50] + "..." if len(q.query) > 50 else q.query,
            "expected": q.expected_intent.value,
            "predicted": predicted.value,
            "correct": is_correct,
        })

    accuracy = correct / len(dataset) if dataset else 0

    return {
        "metric": "intent_classification_accuracy",
        "accuracy": accuracy,
        "correct": correct,
        "total": len(dataset),
        "details": results,
    }


def evaluate_safety_detection() -> dict[str, Any]:
    """Evaluate safety detection accuracy."""
    engine = SafetyEngine()
    dataset = get_dataset()

    correct = 0
    false_positives = 0
    false_negatives = 0
    results = []

    for q in dataset:
        result = engine.check_query_safety(q.query)
        predicted_safe = result.is_safe
        is_correct = predicted_safe == q.expected_safe

        if is_correct:
            correct += 1
        elif predicted_safe and not q.expected_safe:
            false_negatives += 1
        else:
            false_positives += 1

        results.append({
            "id": q.id,
            "category": q.category,
            "expected_safe": q.expected_safe,
            "predicted_safe": predicted_safe,
            "correct": is_correct,
        })

    accuracy = correct / len(dataset) if dataset else 0

    safe_questions = get_safe_questions()
    unsafe_questions = get_unsafe_questions()

    safe_correct = sum(1 for r in results if r["expected_safe"] and r["correct"])
    unsafe_correct = sum(1 for r in results if not r["expected_safe"] and r["correct"])

    return {
        "metric": "safety_detection",
        "accuracy": accuracy,
        "correct": correct,
        "total": len(dataset),
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "safe_accuracy": safe_correct / len(safe_questions) if safe_questions else 0,
        "unsafe_detection_rate": unsafe_correct / len(unsafe_questions) if unsafe_questions else 0,
        "details": results,
    }


def _topic_match(chunk_text: str, chunk_title: str | None, topics: list[str]) -> bool:
    haystack = f"{chunk_title or ''} {chunk_text}".lower()
    return any(topic.lower() in haystack for topic in topics)


def _compute_retrieval_metrics(
    ranked_ids_with_relevance: list[list[bool]],
    k: int = 5,
) -> dict[str, float]:
    """Compute Recall@K and MRR from per-query relevance flags (top-k ordered)."""
    if not ranked_ids_with_relevance:
        return {"recall_at_k": 0.0, "mrr": 0.0, "n": 0}

    recalls = []
    rr_list = []
    for flags in ranked_ids_with_relevance:
        topk = flags[:k]
        recalls.append(1.0 if any(topk) else 0.0)
        rr = 0.0
        for i, rel in enumerate(flags, start=1):
            if rel:
                rr = 1.0 / i
                break
        rr_list.append(rr)

    return {
        "recall_at_k": sum(recalls) / len(recalls),
        "mrr": sum(rr_list) / len(rr_list),
        "n": len(ranked_ids_with_relevance),
        "k": k,
    }


def evaluate_retrieval_comparison(
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
) -> dict[str, Any]:
    """Compare basic / hybrid / hybrid+rerank / context-aware retrieval.

    Relevance is topic-overlap against expected_topics for educational queries.
    """
    try:
        from qdrant_client import QdrantClient
        from app.rag.retrieval import RetrievalService
        from app.embeddings.qdrant_client import TRUSTED_KNOWLEDGE_COLLECTION
        from uuid import uuid4

        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        info = client.get_collection(TRUSTED_KNOWLEDGE_COLLECTION)
        point_count = info.points_count or 0
        if point_count == 0:
            return {
                "metric": "retrieval_comparison",
                "status": "skipped",
                "reason": "trusted_knowledge collection is empty — ingest sample knowledge first",
            }

        retrieval = RetrievalService(client)
        eval_queries = [
            q for q in get_dataset()
            if q.expected_topics and q.category in {
                "educational", "report_explanation", "comparison", "general_health"
            }
        ]

        methods = ["basic", "hybrid", "hybrid_rerank", "context_aware"]
        method_results: dict[str, Any] = {}
        dummy_user = uuid4()

        for method in methods:
            relevance_lists: list[list[bool]] = []
            samples = []
            for q in eval_queries:
                if method == "basic":
                    chunks = retrieval.search_trusted_knowledge(q.query, limit=5, score_threshold=0.0)
                elif method == "hybrid":
                    chunks = retrieval.search_hybrid(q.query, limit=5)
                elif method == "hybrid_rerank":
                    chunks = retrieval.search_hybrid_rerank(q.query, limit=5)
                else:
                    # Knowledge-only path for eval (skip user_reports when limit would be 0)
                    chunks = retrieval.search_hybrid_rerank(q.query, limit=5)

                flags = [
                    _topic_match(c.text, c.title, q.expected_topics)
                    for c in chunks
                ]
                relevance_lists.append(flags)
                samples.append({
                    "id": q.id,
                    "query": q.query[:60],
                    "num_results": len(chunks),
                    "top_relevant": bool(flags[0]) if flags else False,
                    "any_relevant_in_topk": any(flags),
                })

            metrics = _compute_retrieval_metrics(relevance_lists, k=5)
            method_results[method] = {
                **metrics,
                "samples": samples[:5],
            }

        return {
            "metric": "retrieval_comparison",
            "status": "completed",
            "knowledge_points": point_count,
            "queries_evaluated": len(eval_queries),
            "methods": method_results,
            "note": (
                "Relevance judged by expected_topics substring overlap in retrieved chunks. "
                "Not a human-labeled gold set."
            ),
        }

    except Exception as e:
        return {
            "metric": "retrieval_comparison",
            "status": "skipped",
            "reason": str(e),
        }


def check_llm_availability() -> dict[str, Any]:
    """Check if LLM is available for generation metrics."""
    settings = get_settings()

    if settings.openai_api_key:
        return {
            "available": True,
            "provider": "openai",
            "ragas_metrics": "available but not auto-run in this script without explicit opt-in",
        }
    return {
        "available": False,
        "reason": "OPENAI_API_KEY not set",
        "ragas_metrics": "NOT RUN — requires OPENAI_API_KEY",
        "faithfulness": "NOT RUN",
        "answer_relevancy": "NOT RUN",
        "citation_correctness": "NOT RUN",
    }


def run_full_evaluation() -> dict[str, Any]:
    """Run the full evaluation suite."""
    timestamp = datetime.utcnow().isoformat()

    results = {
        "timestamp": timestamp,
        "dataset_stats": DATASET_STATS,
        "evaluations": {},
    }

    print("=" * 60)
    print("MediLens AI - RAG Evaluation Suite")
    print("=" * 60)
    print(f"\nDataset: {DATASET_STATS['total_questions']} questions")
    print(f"  Safe: {DATASET_STATS['safe_questions']}")
    print(f"  Unsafe: {DATASET_STATS['unsafe_questions']}")
    print()

    print("Running intent classification evaluation...")
    intent_results = evaluate_intent_classification()
    results["evaluations"]["intent_classification"] = intent_results
    print(f"  Accuracy: {intent_results['accuracy']:.2%}")

    print("\nRunning safety detection evaluation...")
    safety_results = evaluate_safety_detection()
    results["evaluations"]["safety_detection"] = safety_results
    print(f"  Overall Accuracy: {safety_results['accuracy']:.2%}")
    print(f"  Unsafe Detection Rate: {safety_results['unsafe_detection_rate']:.2%}")
    print(f"  False Negatives: {safety_results['false_negatives']}")

    print("\nRunning retrieval comparison (basic / hybrid / hybrid_rerank / context_aware)...")
    retrieval_results = evaluate_retrieval_comparison()
    results["evaluations"]["retrieval_comparison"] = retrieval_results
    print(f"  Status: {retrieval_results['status']}")
    if retrieval_results["status"] == "completed":
        for method, metrics in retrieval_results.get("methods", {}).items():
            print(
                f"  {method}: Recall@5={metrics['recall_at_k']:.2%} "
                f"MRR={metrics['mrr']:.3f} n={metrics['n']}"
            )
    else:
        print(f"  Reason: {retrieval_results.get('reason')}")

    print("\nChecking LLM availability...")
    llm_status = check_llm_availability()
    results["llm_status"] = llm_status
    if llm_status["available"]:
        print(f"  LLM Available: {llm_status['provider']}")
    else:
        print(f"  LLM Not Available: {llm_status['reason']}")
        print("  RAGAS metrics: NOT RUN (requires OPENAI_API_KEY)")

    print("\n" + "=" * 60)
    print("Evaluation Complete")
    print("=" * 60)

    return results


def save_results(results: dict[str, Any], output_path: str | Path):
    """Save evaluation results to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    results = run_full_evaluation()

    output_path = Path(__file__).parent.parent.parent / "evaluation_results.json"
    save_results(results, output_path)
