"""RAG Evaluator for end-to-end pipeline evaluation."""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.evaluation.metrics import (
    RetrievalMetrics,
    GenerationMetrics,
    calculate_recall_at_k,
    calculate_mrr,
    calculate_hit_rate,
    calculate_context_precision,
    calculate_citation_correctness,
)
from app.safety import SafetyEngine, IntentType

logger = get_logger(__name__)


@dataclass
class EvaluationCase:
    """A single evaluation case."""
    query: str
    expected_relevant_ids: set[str]
    expected_answer_contains: list[str] | None = None
    expected_intent: IntentType | None = None
    expected_safe: bool = True


@dataclass
class EvaluationResult:
    """Result of evaluating a single case."""
    case: EvaluationCase
    retrieval_metrics: RetrievalMetrics
    generation_metrics: GenerationMetrics
    passed: bool
    details: dict[str, Any]


class RAGEvaluator:
    """Evaluator for RAG pipeline quality."""
    
    def __init__(self):
        self.safety_engine = SafetyEngine()
    
    def evaluate_retrieval(
        self,
        case: EvaluationCase,
        retrieved_ids: list[str],
    ) -> RetrievalMetrics:
        """Evaluate retrieval quality for a case.
        
        Args:
            case: Evaluation case with expected relevant IDs
            retrieved_ids: List of retrieved document IDs
            
        Returns:
            RetrievalMetrics
        """
        relevant = case.expected_relevant_ids
        
        recall_at_k = {}
        for k in [1, 3, 5, 10]:
            recall_at_k[k] = calculate_recall_at_k(retrieved_ids, relevant, k)
        
        return RetrievalMetrics(
            recall_at_k=recall_at_k,
            mrr=calculate_mrr(retrieved_ids, relevant),
            context_precision=calculate_context_precision(retrieved_ids, relevant),
            context_recall=calculate_recall_at_k(retrieved_ids, relevant, len(retrieved_ids)),
            hit_rate=calculate_hit_rate(retrieved_ids, relevant),
        )
    
    def evaluate_generation(
        self,
        case: EvaluationCase,
        answer: str,
        citations: list[str],
        source_contents: dict[str, str] | None = None,
    ) -> GenerationMetrics:
        """Evaluate generation quality for a case.
        
        Args:
            case: Evaluation case
            answer: Generated answer
            citations: List of citation URLs
            source_contents: Optional map of URL to content
            
        Returns:
            GenerationMetrics
        """
        answer_relevancy = 0.0
        if case.expected_answer_contains:
            found = sum(
                1 for phrase in case.expected_answer_contains
                if phrase.lower() in answer.lower()
            )
            answer_relevancy = found / len(case.expected_answer_contains)
        
        safety_result = self.safety_engine.check_query_safety(case.query)
        response_safe, _ = self.safety_engine.validate_response(answer)
        
        safety_compliance = 1.0
        if case.expected_safe:
            if not response_safe:
                safety_compliance = 0.0
        
        citation_correctness = 0.0
        if citations and source_contents:
            citation_correctness = calculate_citation_correctness(
                citations, answer, source_contents
            )
        elif citations:
            citation_correctness = 0.5
        
        return GenerationMetrics(
            faithfulness=0.0,
            answer_relevancy=answer_relevancy,
            citation_correctness=citation_correctness,
            safety_compliance=safety_compliance,
        )
    
    def evaluate_case(
        self,
        case: EvaluationCase,
        retrieved_ids: list[str],
        answer: str,
        citations: list[str],
        source_contents: dict[str, str] | None = None,
    ) -> EvaluationResult:
        """Evaluate a complete case end-to-end.
        
        Args:
            case: Evaluation case
            retrieved_ids: Retrieved document IDs
            answer: Generated answer
            citations: Citation URLs
            source_contents: Map of URL to content
            
        Returns:
            EvaluationResult
        """
        retrieval_metrics = self.evaluate_retrieval(case, retrieved_ids)
        generation_metrics = self.evaluate_generation(
            case, answer, citations, source_contents
        )
        
        passed = (
            retrieval_metrics.hit_rate > 0 and
            generation_metrics.safety_compliance >= 1.0
        )
        
        details = {
            "retrieval": retrieval_metrics.to_dict(),
            "generation": generation_metrics.to_dict(),
        }
        
        return EvaluationResult(
            case=case,
            retrieval_metrics=retrieval_metrics,
            generation_metrics=generation_metrics,
            passed=passed,
            details=details,
        )
    
    def evaluate_batch(
        self,
        cases: list[EvaluationCase],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Evaluate a batch of cases.
        
        Args:
            cases: List of evaluation cases
            results: List of RAG results (must match cases)
            
        Returns:
            Aggregated metrics
        """
        if len(cases) != len(results):
            raise ValueError("Cases and results must have same length")
        
        eval_results = []
        for case, result in zip(cases, results):
            eval_result = self.evaluate_case(
                case=case,
                retrieved_ids=result.get("retrieved_ids", []),
                answer=result.get("answer", ""),
                citations=result.get("citations", []),
                source_contents=result.get("source_contents"),
            )
            eval_results.append(eval_result)
        
        passed_count = sum(1 for r in eval_results if r.passed)
        
        avg_retrieval = {
            "mrr": sum(r.retrieval_metrics.mrr for r in eval_results) / len(eval_results),
            "hit_rate": sum(r.retrieval_metrics.hit_rate for r in eval_results) / len(eval_results),
        }
        
        avg_generation = {
            "answer_relevancy": sum(r.generation_metrics.answer_relevancy for r in eval_results) / len(eval_results),
            "safety_compliance": sum(r.generation_metrics.safety_compliance for r in eval_results) / len(eval_results),
        }
        
        return {
            "total_cases": len(cases),
            "passed": passed_count,
            "pass_rate": passed_count / len(cases),
            "avg_retrieval_metrics": avg_retrieval,
            "avg_generation_metrics": avg_generation,
        }
