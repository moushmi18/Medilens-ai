"""Tests for evaluation metrics."""
import pytest

from app.evaluation.metrics import (
    calculate_recall_at_k,
    calculate_mrr,
    calculate_hit_rate,
    calculate_context_precision,
)
from app.evaluation.evaluator import RAGEvaluator, EvaluationCase
from app.safety import IntentType


class TestRetrievalMetrics:
    """Tests for retrieval metrics."""
    
    def test_recall_at_k_perfect(self):
        """Perfect recall when all relevant docs retrieved."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"a", "b", "c"}
        
        assert calculate_recall_at_k(retrieved, relevant, 3) == 1.0
        assert calculate_recall_at_k(retrieved, relevant, 5) == 1.0
    
    def test_recall_at_k_partial(self):
        """Partial recall when some relevant docs retrieved."""
        retrieved = ["a", "x", "y", "b", "z"]
        relevant = {"a", "b", "c"}
        
        assert calculate_recall_at_k(retrieved, relevant, 1) == pytest.approx(1/3)
        assert calculate_recall_at_k(retrieved, relevant, 4) == pytest.approx(2/3)
    
    def test_recall_at_k_zero(self):
        """Zero recall when no relevant docs retrieved."""
        retrieved = ["x", "y", "z"]
        relevant = {"a", "b", "c"}
        
        assert calculate_recall_at_k(retrieved, relevant, 3) == 0.0
    
    def test_mrr_first_position(self):
        """MRR = 1 when first result is relevant."""
        retrieved = ["a", "b", "c"]
        relevant = {"a"}
        
        assert calculate_mrr(retrieved, relevant) == 1.0
    
    def test_mrr_second_position(self):
        """MRR = 0.5 when second result is relevant."""
        retrieved = ["x", "a", "b"]
        relevant = {"a"}
        
        assert calculate_mrr(retrieved, relevant) == 0.5
    
    def test_mrr_no_match(self):
        """MRR = 0 when no relevant results."""
        retrieved = ["x", "y", "z"]
        relevant = {"a"}
        
        assert calculate_mrr(retrieved, relevant) == 0.0
    
    def test_hit_rate_found(self):
        """Hit rate = 1 when any relevant doc found."""
        retrieved = ["x", "a", "y"]
        relevant = {"a", "b"}
        
        assert calculate_hit_rate(retrieved, relevant) == 1.0
    
    def test_hit_rate_not_found(self):
        """Hit rate = 0 when no relevant doc found."""
        retrieved = ["x", "y", "z"]
        relevant = {"a", "b"}
        
        assert calculate_hit_rate(retrieved, relevant) == 0.0
    
    def test_context_precision(self):
        """Context precision calculation."""
        retrieved = ["a", "b", "x", "y"]
        relevant = {"a", "b", "c"}
        
        assert calculate_context_precision(retrieved, relevant) == 0.5


class TestEvaluator:
    """Tests for RAG evaluator."""
    
    @pytest.fixture
    def evaluator(self):
        return RAGEvaluator()
    
    def test_evaluate_retrieval(self, evaluator):
        """Evaluate retrieval metrics."""
        case = EvaluationCase(
            query="What is cholesterol?",
            expected_relevant_ids={"doc1", "doc2"},
        )
        
        retrieved = ["doc1", "doc3", "doc2", "doc4"]
        
        metrics = evaluator.evaluate_retrieval(case, retrieved)
        
        assert metrics.hit_rate == 1.0
        assert metrics.mrr == 1.0
        assert metrics.recall_at_k[1] == 0.5
        assert metrics.recall_at_k[3] == 1.0
    
    def test_evaluate_generation_relevancy(self, evaluator):
        """Evaluate generation with relevancy check."""
        case = EvaluationCase(
            query="What is hemoglobin?",
            expected_relevant_ids=set(),
            expected_answer_contains=["protein", "blood", "oxygen"],
        )
        
        answer = "Hemoglobin is a protein in red blood cells that carries oxygen."
        
        metrics = evaluator.evaluate_generation(case, answer, [])
        
        assert metrics.answer_relevancy == 1.0
    
    def test_evaluate_generation_partial_relevancy(self, evaluator):
        """Evaluate generation with partial relevancy."""
        case = EvaluationCase(
            query="What is hemoglobin?",
            expected_relevant_ids=set(),
            expected_answer_contains=["protein", "blood", "transport", "iron"],
        )
        
        answer = "Hemoglobin is a protein found in blood."
        
        metrics = evaluator.evaluate_generation(case, answer, [])
        
        assert metrics.answer_relevancy == 0.5
    
    def test_evaluate_case_safety(self, evaluator):
        """Evaluate safety compliance."""
        case = EvaluationCase(
            query="What is HDL cholesterol?",
            expected_relevant_ids={"doc1"},
            expected_safe=True,
        )
        
        safe_answer = "HDL cholesterol is often called 'good' cholesterol."
        
        result = evaluator.evaluate_case(
            case=case,
            retrieved_ids=["doc1"],
            answer=safe_answer,
            citations=[],
        )
        
        assert result.generation_metrics.safety_compliance == 1.0
    
    def test_batch_evaluation(self, evaluator):
        """Evaluate batch of cases."""
        cases = [
            EvaluationCase(
                query="What is HDL?",
                expected_relevant_ids={"doc1"},
            ),
            EvaluationCase(
                query="What is LDL?",
                expected_relevant_ids={"doc2"},
            ),
        ]
        
        results = [
            {"retrieved_ids": ["doc1"], "answer": "HDL is good cholesterol.", "citations": []},
            {"retrieved_ids": ["doc3"], "answer": "LDL is bad cholesterol.", "citations": []},
        ]
        
        batch_result = evaluator.evaluate_batch(cases, results)
        
        assert batch_result["total_cases"] == 2
        assert batch_result["pass_rate"] == 0.5
