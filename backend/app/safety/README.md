# Safety Module

Safety engine for medical content guardrails.

## Components (Phase 8)

- `intent_classifier.py` - Query intent classification
- `safety_rules.py` - Non-negotiable safety rule enforcement
- `emergency_detector.py` - Emergency symptom detection
- `injection_defense.py` - Prompt injection prevention
- `disclaimers.py` - Appropriate disclaimer generation

## Safety Categories

1. Educational - Allow with sources
2. Report Explanation - Allow with report context
3. Comparison - Allow with constraints
4. Diagnosis Request - Refuse
5. Medication Request - Refuse
6. Emergency - Immediate guidance

## Critical Rules

- Never diagnose
- Never prescribe
- Never recommend dosages
- Never conclude disease from labs
- Never fabricate ranges or claims
- Always communicate uncertainty
- Always refer to professionals
