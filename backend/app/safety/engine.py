"""Safety engine for intent classification and response validation.

CRITICAL: This module enforces that MediLens AI:
- NEVER diagnoses conditions
- NEVER prescribes medications
- NEVER recommends dosages
- ALWAYS redirects medical decisions to healthcare providers
"""
from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Classification of user query intent."""
    EDUCATIONAL = "educational"
    REPORT_EXPLANATION = "report_explanation"
    COMPARISON = "comparison"
    DIAGNOSIS_REQUEST = "diagnosis_request"
    MEDICATION_REQUEST = "medication_request"
    EMERGENCY = "emergency"
    GENERAL_HEALTH = "general_health"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass
class SafetyResult:
    """Result of safety check."""
    is_safe: bool
    intent: IntentType
    message: Optional[str] = None
    should_redirect: bool = False
    emergency_detected: bool = False


DIAGNOSIS_PATTERNS = [
    r"do i have\s+\w+",
    r"is this\s+\w+\s*(disease|condition|cancer|disorder|syndrome)?",
    r"what('s| is) wrong with me",
    r"am i (sick|dying|ill)",
    r"diagnose (me|my)",
    r"tell me (what|if) i have",
    r"does this mean i have",
]

MEDICATION_PATTERNS = [
    r"what (medication|medicine|drug) should i (take|use)",
    r"prescribe (me|something)",
    r"what dose should i",
    r"should i (take|stop|change) my (medication|medicine)",
    r"how (much|many) (should|can) i take",
    r"can i take\s+\w+\s+with\s+\w+",
    r"recommend.*(medication|drug|medicine|supplement)",
    r"what (pills|tablets) (for|to)",
]

EMERGENCY_PATTERNS = [
    r"(kill|hurt|harm)\s*(myself|me)",
    r"suicid(e|al)",
    r"end (my|it all|everything)",
    r"want to die",
    r"chest pain",
    r"heart attack",
    r"can'?t breathe",
    r"stroke",
    r"overdos",
    r"severe (pain|bleeding)",
    r"unconscious",
    r"seizure",
]

EDUCATIONAL_PATTERNS = [
    r"what (is|are|does)\s+\w+",
    r"explain\s+\w+",
    r"meaning of\s+\w+",
    r"what do(es)? (my|the|this) (result|level|value)",
    r"understand(ing)?\s+(my|the)",
    r"help me understand",
    r"normal range (for|of)",
    r"reference range",
]

COMPARISON_PATTERNS = [
    r"compare\s+\w+",
    r"(better|worse) than (last|before|previous)",
    r"change(d|s)? (from|since)",
    r"trend",
    r"over time",
    r"progression",
]


SAFE_INTENTS = {
    IntentType.EDUCATIONAL,
    IntentType.REPORT_EXPLANATION,
    IntentType.COMPARISON,
    IntentType.GENERAL_HEALTH,
}

REDIRECT_MESSAGE = (
    "I'm designed to help you understand your medical reports for educational "
    "purposes. For medical advice, diagnosis, or treatment decisions, please "
    "consult with your healthcare provider."
)

EMERGENCY_MESSAGE = (
    "⚠️ If you're experiencing a medical emergency, please call emergency "
    "services immediately (911 in the US, 999 in the UK) or go to your "
    "nearest emergency room. For mental health crisis, contact the "
    "National Suicide Prevention Lifeline at 988 (US) or Samaritans at "
    "116 123 (UK)."
)


class SafetyEngine:
    """Engine for classifying intent and ensuring safe responses."""
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self._diagnosis_re = [re.compile(p, re.IGNORECASE) for p in DIAGNOSIS_PATTERNS]
        self._medication_re = [re.compile(p, re.IGNORECASE) for p in MEDICATION_PATTERNS]
        self._emergency_re = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]
        self._educational_re = [re.compile(p, re.IGNORECASE) for p in EDUCATIONAL_PATTERNS]
        self._comparison_re = [re.compile(p, re.IGNORECASE) for p in COMPARISON_PATTERNS]
    
    def _match_patterns(self, text: str, patterns: list[re.Pattern]) -> bool:
        """Check if text matches any pattern."""
        return any(p.search(text) for p in patterns)
    
    def classify_intent(self, query: str) -> IntentType:
        """Classify the intent of a user query.
        
        Args:
            query: User's query text
            
        Returns:
            IntentType classification
        """
        if self._match_patterns(query, self._emergency_re):
            return IntentType.EMERGENCY
        
        if self._match_patterns(query, self._diagnosis_re):
            return IntentType.DIAGNOSIS_REQUEST
        
        if self._match_patterns(query, self._medication_re):
            return IntentType.MEDICATION_REQUEST
        
        if self._match_patterns(query, self._comparison_re):
            return IntentType.COMPARISON
        
        if self._match_patterns(query, self._educational_re):
            return IntentType.EDUCATIONAL
        
        report_keywords = ["report", "result", "lab", "test", "level", "value"]
        if any(kw in query.lower() for kw in report_keywords):
            return IntentType.REPORT_EXPLANATION
        
        return IntentType.GENERAL_HEALTH
    
    def check_query_safety(self, query: str) -> SafetyResult:
        """Check if a query is safe to process.
        
        Args:
            query: User's query text
            
        Returns:
            SafetyResult with classification and guidance
        """
        intent = self.classify_intent(query)
        
        if intent == IntentType.EMERGENCY:
            logger.warning("emergency_intent_detected", query=query[:50])
            return SafetyResult(
                is_safe=False,
                intent=intent,
                message=EMERGENCY_MESSAGE,
                emergency_detected=True,
            )
        
        if intent == IntentType.DIAGNOSIS_REQUEST:
            logger.info("diagnosis_request_detected", query=query[:50])
            return SafetyResult(
                is_safe=False,
                intent=intent,
                message=REDIRECT_MESSAGE,
                should_redirect=True,
            )
        
        if intent == IntentType.MEDICATION_REQUEST:
            logger.info("medication_request_detected", query=query[:50])
            return SafetyResult(
                is_safe=False,
                intent=intent,
                message=REDIRECT_MESSAGE,
                should_redirect=True,
            )
        
        return SafetyResult(
            is_safe=True,
            intent=intent,
        )
    
    def validate_response(self, response: str) -> tuple[bool, Optional[str]]:
        """Validate that a generated response is safe.
        
        Checks that the response doesn't contain diagnosis or prescription
        language that might have slipped through.
        
        Args:
            response: Generated response text
            
        Returns:
            Tuple of (is_safe, warning_message)
        """
        dangerous_phrases = [
            r"you (have|are suffering from|are diagnosed with)\s+\w+",
            r"this (is|means you have)\s+(cancer|diabetes|disease|disorder)",
            r"take \d+ (mg|ml|pills|tablets)",
            r"I (recommend|prescribe|suggest)\s+(taking|starting)\s+\w+",
            r"increase your (dose|dosage) to",
            r"stop taking your",
        ]
        
        for pattern in dangerous_phrases:
            if re.search(pattern, response, re.IGNORECASE):
                logger.warning(
                    "unsafe_response_detected",
                    pattern=pattern,
                    response_preview=response[:100],
                )
                return False, "Response contains potentially unsafe medical advice"
        
        return True, None
    
    def add_disclaimer(self, response: str) -> str:
        """Add educational disclaimer to response if not present."""
        disclaimer = (
            "\n\n---\n*This information is for educational purposes only and "
            "should not be considered medical advice. Please consult with a "
            "healthcare professional for medical decisions.*"
        )
        
        if "educational purposes" not in response.lower():
            return response + disclaimer
        
        return response
