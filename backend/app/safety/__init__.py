"""Safety module for medical AI responses.

Implements intent classification and safety guardrails to ensure
the system NEVER diagnoses, prescribes, or recommends dosages.
"""
from .engine import SafetyEngine, IntentType, SafetyResult

__all__ = ["SafetyEngine", "IntentType", "SafetyResult"]
