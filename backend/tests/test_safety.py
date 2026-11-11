"""Tests for safety engine."""
import pytest

from app.safety import SafetyEngine, IntentType


class TestIntentClassification:
    """Tests for intent classification."""
    
    @pytest.fixture
    def engine(self):
        return SafetyEngine()
    
    def test_emergency_suicide(self, engine):
        """Detect suicide-related queries."""
        assert engine.classify_intent("I want to kill myself") == IntentType.EMERGENCY
        assert engine.classify_intent("suicidal thoughts") == IntentType.EMERGENCY
    
    def test_emergency_medical(self, engine):
        """Detect medical emergencies."""
        assert engine.classify_intent("I'm having chest pain") == IntentType.EMERGENCY
        assert engine.classify_intent("having a heart attack") == IntentType.EMERGENCY
    
    def test_diagnosis_request(self, engine):
        """Detect diagnosis requests."""
        assert engine.classify_intent("Do I have diabetes?") == IntentType.DIAGNOSIS_REQUEST
        assert engine.classify_intent("What's wrong with me?") == IntentType.DIAGNOSIS_REQUEST
        assert engine.classify_intent("Diagnose my condition") == IntentType.DIAGNOSIS_REQUEST
    
    def test_medication_request(self, engine):
        """Detect medication requests."""
        assert engine.classify_intent("What medication should I take?") == IntentType.MEDICATION_REQUEST
        assert engine.classify_intent("Prescribe me something") == IntentType.MEDICATION_REQUEST
        assert engine.classify_intent("What dose should I take?") == IntentType.MEDICATION_REQUEST
    
    def test_educational(self, engine):
        """Detect educational queries."""
        assert engine.classify_intent("What is cholesterol?") == IntentType.EDUCATIONAL
        assert engine.classify_intent("Explain hemoglobin to me") == IntentType.EDUCATIONAL
        assert engine.classify_intent("What does my result mean?") == IntentType.EDUCATIONAL
    
    def test_comparison(self, engine):
        """Detect comparison queries."""
        assert engine.classify_intent("Compare my results over time") == IntentType.COMPARISON
        assert engine.classify_intent("How have my results changed from last time?") == IntentType.COMPARISON
    
    def test_report_explanation(self, engine):
        """Detect report explanation queries."""
        assert engine.classify_intent("What do my lab results show?") == IntentType.REPORT_EXPLANATION
        assert engine.classify_intent("Can you tell me about my test results?") == IntentType.REPORT_EXPLANATION


class TestQuerySafety:
    """Tests for query safety checking."""
    
    @pytest.fixture
    def engine(self):
        return SafetyEngine()
    
    def test_safe_educational_query(self, engine):
        """Educational queries are safe."""
        result = engine.check_query_safety("What is HDL cholesterol?")
        assert result.is_safe
        assert result.intent == IntentType.EDUCATIONAL
    
    def test_unsafe_diagnosis_query(self, engine):
        """Diagnosis queries are not safe."""
        result = engine.check_query_safety("Do I have cancer?")
        assert not result.is_safe
        assert result.intent == IntentType.DIAGNOSIS_REQUEST
        assert result.should_redirect
    
    def test_unsafe_medication_query(self, engine):
        """Medication queries are not safe."""
        result = engine.check_query_safety("What medication should I take for this?")
        assert not result.is_safe
        assert result.intent == IntentType.MEDICATION_REQUEST
        assert result.should_redirect
    
    def test_emergency_query(self, engine):
        """Emergency queries are flagged."""
        result = engine.check_query_safety("I want to hurt myself")
        assert not result.is_safe
        assert result.intent == IntentType.EMERGENCY
        assert result.emergency_detected
        assert "emergency" in result.message.lower()


class TestResponseValidation:
    """Tests for response validation."""
    
    @pytest.fixture
    def engine(self):
        return SafetyEngine()
    
    def test_safe_educational_response(self, engine):
        """Safe educational response passes."""
        response = (
            "Cholesterol is a waxy substance found in your blood. "
            "HDL is often called 'good' cholesterol because it helps "
            "remove other forms of cholesterol from your bloodstream."
        )
        is_safe, warning = engine.validate_response(response)
        assert is_safe
        assert warning is None
    
    def test_unsafe_diagnosis_response(self, engine):
        """Response with diagnosis is unsafe."""
        response = "Based on your results, you have diabetes."
        is_safe, warning = engine.validate_response(response)
        assert not is_safe
        assert warning is not None
    
    def test_unsafe_prescription_response(self, engine):
        """Response with prescription is unsafe."""
        response = "I recommend taking 500mg of metformin daily."
        is_safe, warning = engine.validate_response(response)
        assert not is_safe


class TestDisclaimer:
    """Tests for disclaimer handling."""
    
    @pytest.fixture
    def engine(self):
        return SafetyEngine()
    
    def test_adds_disclaimer(self, engine):
        """Adds disclaimer when not present."""
        response = "Hemoglobin is a protein in red blood cells."
        result = engine.add_disclaimer(response)
        assert "educational purposes" in result.lower()
    
    def test_preserves_existing_disclaimer(self, engine):
        """Doesn't duplicate existing disclaimer."""
        response = "This is for educational purposes only."
        result = engine.add_disclaimer(response)
        assert result.count("educational purposes") == 1
