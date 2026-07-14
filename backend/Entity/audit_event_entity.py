import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from Config.database import Base


class AuditEvent(Base):
    """
    Append-only audit trail record (FR-022, NFR-001).

    This table has NO TimestampMixin — it has its own immutable timestamp
    field and deliberately no updated_at column to enforce append-only semantics.
    No row in this table is ever updated or deleted.

    actor_user_id:  the platform user who triggered the event (nullable for
                    system/channel-originated events).
    actor_channel:  set when the event was triggered by a channel adapter
                    OR an automated pipeline step (e.g. "ai_classifier",
                    "auto_router") rather than an authenticated user.
    object_type:    the domain entity affected (e.g. "case", "recommendation").
    object_id:      the PK of the affected entity stored as text to support
                    both UUID and integer PKs.
    before_hash:    SHA-256 of the record state before the change (tamper
                    evidence — deliberately one-way, see Utils/hashing.py).
    after_hash:     SHA-256 of the record state after the change.
    detail:         small, human-readable, non-PII summary of what changed
                    (e.g. {"from": "ROUTED", "to": "ASSIGNED", "reason": "..."})
                    — separate from before/after_hash so the roadmap UI can
                    show "what happened" without weakening the tamper-evident
                    hash, and safe to show even in the citizen-redacted view.
    """
    __tablename__ = "audit_events"

    id             = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    actor_user_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_channel  = Column(String, nullable=True)
    action         = Column(String, nullable=False, index=True)
    object_type    = Column(String, nullable=False, index=True)
    object_id      = Column(Text, nullable=False)
    before_hash    = Column(String, nullable=True)
    after_hash     = Column(String, nullable=True)
    ip_address     = Column(String, nullable=True)
    detail         = Column(JSON, nullable=True)
    timestamp      = Column(DateTime(timezone=True), nullable=False, index=True)
