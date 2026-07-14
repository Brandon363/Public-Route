from dataclasses import dataclass
from typing import Optional

from Utils.Enums import UrgencyEnum
from Utils.service_categories import (
    CATEGORY_KEYWORDS,
    DEFAULT_CATEGORY,
    HIGH_URGENCY_KEYWORDS,
    CRITICAL_URGENCY_KEYWORDS,
)

# Below this confidence, CaseService routes the case to MANUAL_REVIEW instead
# of auto-advancing to CLASSIFIED/ROUTED (AI-004 abstention requirement).
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.55


@dataclass
class ClassificationResult:
    category: str
    subcategory: Optional[str]
    urgency: str
    confidence: float


def classify(description: str) -> ClassificationResult:
    """
    Rule-based keyword classifier — the explicit baseline referenced by
    AI-002 ("compare against a simple baseline"). Not a trained model; a
    real classifier is P1 roadmap work once labelled data is available.

    No DB access — pure function so it's trivially unit-testable and easy
    to swap for a model-backed implementation later without touching
    CaseService's call site.
    """
    text = description.lower()

    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        matches = sum(1 for keyword in keywords if keyword in text)
        if matches:
            scores[category] = matches

    urgency = _infer_urgency(text)

    if not scores:
        return ClassificationResult(
            category=DEFAULT_CATEGORY, subcategory=None, urgency=urgency, confidence=0.0
        )

    top_score = max(scores.values())
    top_categories = [c for c, s in scores.items() if s == top_score]

    # Two keyword hits reaches full confidence; one hit alone stays below
    # the abstention threshold. Ties across categories dilute confidence
    # proportionally, since the match is genuinely ambiguous.
    confidence = min(1.0, top_score / 2)
    if len(top_categories) > 1:
        confidence = confidence / len(top_categories)

    return ClassificationResult(
        category=top_categories[0],
        subcategory=None,
        urgency=urgency,
        confidence=round(confidence, 2),
    )


def _infer_urgency(text: str) -> str:
    if any(keyword in text for keyword in CRITICAL_URGENCY_KEYWORDS):
        return UrgencyEnum.CRITICAL.value
    if any(keyword in text for keyword in HIGH_URGENCY_KEYWORDS):
        return UrgencyEnum.HIGH.value
    return UrgencyEnum.MEDIUM.value
