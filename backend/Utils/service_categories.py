from datetime import timedelta

# ---------------------------------------------------------------------------
# Placeholder service-category taxonomy for the rule-based classification
# baseline (Service/classification_service.py).
#
# This is NOT sourced from the real AI4I `public_service_requests` dataset —
# that dataset is not present in this repository checkout. Replace these
# keyword lists (or the categories themselves) with the authoritative
# taxonomy once the dataset/data dictionary is onboarded (DR-001).
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "water_sanitation": [
        "water", "leak", "leaking", "pipe", "burst", "sewage", "sewer",
        "drain", "drainage", "borehole", "tap", "toilet", "sanitation",
    ],
    "roads_infrastructure": [
        "road", "pothole", "bridge", "streetlight", "street light",
        "traffic light", "pavement", "footbridge", "culvert", "signage",
    ],
    "electricity_power": [
        "power", "electricity", "electric", "transformer", "outage",
        "blackout", "cable", "voltage", "substation",
    ],
    "waste_management": [
        "refuse", "garbage", "rubbish", "trash", "waste", "dumping",
        "dumpsite", "litter", "bin",
    ],
    "health_services": [
        "clinic", "hospital", "health", "medicine", "medication",
        "nurse", "doctor", "ambulance",
    ],
    "security_safety": [
        "crime", "theft", "assault", "robbery", "unsafe", "violence",
        "security", "fire", "collapse", "collapsed",
    ],
}

DEFAULT_CATEGORY = "other"

# Keywords that, if present, push the inferred urgency up from the default.
HIGH_URGENCY_KEYWORDS = [
    "urgent", "emergency", "danger", "dangerous", "collapse", "collapsed",
]
CRITICAL_URGENCY_KEYWORDS = [
    "fire", "explosion", "life-threatening", "dying", "critical",
]

# SLA duration by urgency, applied to Case.sla_deadline at the CLASSIFIED
# transition (FR-011). Placeholder values pending institution-approved SLAs.
URGENCY_SLA: dict[str, timedelta] = {
    "low": timedelta(days=14),
    "medium": timedelta(days=7),
    "high": timedelta(days=2),
    "critical": timedelta(hours=12),
}
