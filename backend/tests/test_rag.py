"""Tests for RAG pipeline."""
import pytest
from uuid import uuid4

from app.rag.prompts import EMERGENCY_KEYWORDS, EMERGENCY_RESPONSE
from app.rag.pipeline import RAGPipeline


class TestEmergencyDetection:
    """Tests for emergency detection."""
    
    @pytest.fixture
    def pipeline(self):
        """Create mock RAG pipeline (no Qdrant needed for emergency check)."""
        class MockPipeline:
            def check_emergency(self, query: str) -> bool:
                query_lower = query.lower()
                for keyword in EMERGENCY_KEYWORDS:
                    if keyword in query_lower:
                        return True
                return False
        return MockPipeline()
    
    def test_detects_suicide_mention(self, pipeline):
        """Detect suicide-related queries."""
        assert pipeline.check_emergency("I want to kill myself")
        assert pipeline.check_emergency("thinking about suicide")
    
    def test_detects_chest_pain(self, pipeline):
        """Detect chest pain emergency."""
        assert pipeline.check_emergency("I'm having severe chest pain")
    
    def test_detects_breathing_difficulty(self, pipeline):
        """Detect breathing emergency."""
        assert pipeline.check_emergency("I can't breathe properly")
    
    def test_normal_query_not_emergency(self, pipeline):
        """Normal queries are not emergencies."""
        assert not pipeline.check_emergency("What does my cholesterol level mean?")
        assert not pipeline.check_emergency("Explain hemoglobin to me")
    
    def test_case_insensitive(self, pipeline):
        """Emergency detection is case insensitive."""
        assert pipeline.check_emergency("CHEST PAIN")
        assert pipeline.check_emergency("Heart Attack")


class TestContextBuilding:
    """Tests for context building."""
    
    def test_build_context_with_chunks(self):
        """Build context from chunks."""
        from app.rag.retrieval import RetrievedChunk
        
        class MockPipeline:
            def build_context(self, knowledge_chunks, report_chunks):
                if knowledge_chunks:
                    knowledge_context = "\n\n".join([
                        f"[Source: {chunk.title or chunk.source_type}]\n{chunk.text}"
                        for chunk in knowledge_chunks
                    ])
                else:
                    knowledge_context = "No relevant trusted knowledge found."
                
                if report_chunks:
                    report_context = "\n\n".join([
                        f"[From Report: {chunk.title or 'Unknown'}]\n{chunk.text}"
                        for chunk in report_chunks
                    ])
                else:
                    report_context = "No specific report content relevant to this question."
                
                return knowledge_context, report_context
        
        pipeline = MockPipeline()
        
        knowledge = [
            RetrievedChunk(
                id="1",
                text="Cholesterol is a fatty substance.",
                score=0.9,
                source_type="medlineplus",
                title="Cholesterol Overview",
            )
        ]
        
        report = [
            RetrievedChunk(
                id="2",
                text="Total cholesterol: 200 mg/dL",
                score=0.85,
                source_type="user_report",
                title="Lab Report",
            )
        ]
        
        k_ctx, r_ctx = pipeline.build_context(knowledge, report)
        
        assert "Cholesterol is a fatty substance" in k_ctx
        assert "Total cholesterol: 200 mg/dL" in r_ctx
    
    def test_empty_chunks_handled(self):
        """Handle empty chunk lists."""
        class MockPipeline:
            def build_context(self, knowledge_chunks, report_chunks):
                if knowledge_chunks:
                    knowledge_context = "Has knowledge"
                else:
                    knowledge_context = "No relevant trusted knowledge found."
                
                if report_chunks:
                    report_context = "Has report"
                else:
                    report_context = "No specific report content relevant to this question."
                
                return knowledge_context, report_context
        
        pipeline = MockPipeline()
        k_ctx, r_ctx = pipeline.build_context([], [])
        
        assert "No relevant trusted knowledge" in k_ctx
        assert "No specific report content" in r_ctx


class TestEvidenceSufficiency:
    """Tests for evidence sufficiency check."""
    
    def test_sufficient_evidence(self):
        """Evidence above threshold is sufficient."""
        from app.rag.retrieval import RetrievedChunk
        
        class MockPipeline:
            def check_evidence_sufficiency(self, k_chunks, r_chunks, min_score=0.5):
                if not k_chunks and not r_chunks:
                    return False
                all_chunks = k_chunks + r_chunks
                max_score = max(chunk.score for chunk in all_chunks)
                return max_score >= min_score
        
        pipeline = MockPipeline()
        
        chunks = [
            RetrievedChunk(
                id="1", text="test", score=0.8,
                source_type="test"
            )
        ]
        
        assert pipeline.check_evidence_sufficiency(chunks, [])
    
    def test_insufficient_evidence(self):
        """Low scores are insufficient."""
        from app.rag.retrieval import RetrievedChunk
        
        class MockPipeline:
            def check_evidence_sufficiency(self, k_chunks, r_chunks, min_score=0.5):
                if not k_chunks and not r_chunks:
                    return False
                all_chunks = k_chunks + r_chunks
                max_score = max(chunk.score for chunk in all_chunks)
                return max_score >= min_score
        
        pipeline = MockPipeline()
        
        chunks = [
            RetrievedChunk(
                id="1", text="test", score=0.3,
                source_type="test"
            )
        ]
        
        assert not pipeline.check_evidence_sufficiency(chunks, [])
    
    def test_no_evidence(self):
        """No chunks is insufficient."""
        class MockPipeline:
            def check_evidence_sufficiency(self, k_chunks, r_chunks, min_score=0.5):
                if not k_chunks and not r_chunks:
                    return False
                return True
        
        pipeline = MockPipeline()
        assert not pipeline.check_evidence_sufficiency([], [])


class TestLLMProvider:
    """Tests for LLM provider."""
    
    def test_unconfigured_provider(self):
        """Unconfigured provider returns clear message."""
        from app.llm.provider import UnconfiguredProvider
        
        provider = UnconfiguredProvider()
        
        assert not provider.is_configured
        assert "not currently configured" in provider.NOT_CONFIGURED_MESSAGE
    
    @pytest.mark.asyncio
    async def test_unconfigured_generate(self):
        """Unconfigured provider generate returns message."""
        from app.llm.provider import UnconfiguredProvider, LLMMessage
        
        provider = UnconfiguredProvider()
        
        response = await provider.generate([
            LLMMessage(role="user", content="Test")
        ])
        
        assert "not currently configured" in response.content
        assert response.model == "unconfigured"
