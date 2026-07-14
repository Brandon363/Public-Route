from enum import Enum


# ---------------------------------------------------------------------------
# Channel — how a citizen or officer submitted a report.
# ---------------------------------------------------------------------------

class ChannelEnum(str, Enum):
    WHATSAPP_TEXT  = "whatsapp_text"
    WHATSAPP_VOICE = "whatsapp_voice"
    WEB            = "web"
    USSD           = "ussd"
    CALL_CENTRE    = "call_centre"
    WALK_IN        = "walk_in"
    DOCUMENT       = "document"
    API            = "api"


# ---------------------------------------------------------------------------
# Consent — citizen agreement status recorded at intake.
# ---------------------------------------------------------------------------

class ConsentStatusEnum(str, Enum):
    GRANTED      = "granted"
    DECLINED     = "declined"
    NOT_REQUIRED = "not_required"


# ---------------------------------------------------------------------------
# Malware scan result for uploaded documents.
# ---------------------------------------------------------------------------

class MalwareStatusEnum(str, Enum):
    PENDING  = "pending"
    CLEAN    = "clean"
    INFECTED = "infected"
    ERROR    = "error"


# ---------------------------------------------------------------------------
# Settlement type — geographic classification for equity analysis.
# ---------------------------------------------------------------------------

class SettlementTypeEnum(str, Enum):
    URBAN      = "urban"
    PERI_URBAN = "peri_urban"
    RURAL      = "rural"


# ---------------------------------------------------------------------------
# Case lifecycle states (FR-011, architecture §5).
# ---------------------------------------------------------------------------

class CaseStatusEnum(str, Enum):
    RECEIVED         = "RECEIVED"
    VALIDATING       = "VALIDATING"
    CLASSIFIED       = "CLASSIFIED"
    ROUTED           = "ROUTED"
    ASSIGNED         = "ASSIGNED"
    IN_PROGRESS      = "IN_PROGRESS"
    RESOLVED         = "RESOLVED"
    CLOSED           = "CLOSED"
    REJECTED         = "REJECTED"
    MANUAL_REVIEW    = "MANUAL_REVIEW"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    ON_HOLD          = "ON_HOLD"
    ESCALATED        = "ESCALATED"
    REOPENED         = "REOPENED"


# ---------------------------------------------------------------------------
# Urgency / severity scale.
# ---------------------------------------------------------------------------

class UrgencyEnum(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class SeverityEnum(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Assignment lifecycle.
# ---------------------------------------------------------------------------

class AssignmentStatusEnum(str, Enum):
    PENDING     = "pending"
    ACCEPTED    = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    CANCELLED   = "cancelled"


# ---------------------------------------------------------------------------
# Notification delivery status.
# ---------------------------------------------------------------------------

class DeliveryStatusEnum(str, Enum):
    QUEUED    = "queued"
    SENT      = "sent"
    DELIVERED = "delivered"
    FAILED    = "failed"
    OPTED_OUT = "opted_out"


# ---------------------------------------------------------------------------
# Model governance lifecycle.
# ---------------------------------------------------------------------------

class ModelStatusEnum(str, Enum):
    TRAINING  = "training"
    VALIDATED = "validated"
    DEPLOYED  = "deployed"
    RETIRED   = "retired"


# ---------------------------------------------------------------------------
# Recommendation lifecycle.
# ---------------------------------------------------------------------------

class RecommendationStatusEnum(str, Enum):
    DRAFT            = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED         = "approved"
    REJECTED         = "rejected"
    IMPLEMENTED      = "implemented"


# ---------------------------------------------------------------------------
# Human approval decisions.
# ---------------------------------------------------------------------------

class ApprovalDecisionEnum(str, Enum):
    APPROVED  = "approved"
    REJECTED  = "rejected"
    MODIFIED  = "modified"