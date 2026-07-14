import uuid
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import CaseStatusEnum, UrgencyEnum


class Case(Base, TimestampMixin):
    """
    Core operational case record.

    Created from a validated Submission after classification. Drives the
    SLA clock, routing, queue assignment and citizen notifications.
    This record is pseudonymised in analytical exports — no direct PII.

    reference_number: human-readable unique code (e.g. SF-2026-00001).
    classification_confidence: 0.0–1.0 score from the classifier.
    sla_deadline: computed from urgency and category SLA policy at creation.
    """
    __tablename__ = "cases"

    id                        = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    reference_number          = Column(String, unique=True, index=True, nullable=False)
    category                  = Column(String, nullable=False)
    subcategory               = Column(String, nullable=True)
    urgency                   = Column(String, nullable=False, default=UrgencyEnum.MEDIUM)
    status                    = Column(
        String, nullable=False, default=CaseStatusEnum.RECEIVED, index=True
    )
    description               = Column(Text, nullable=False)
    english_description       = Column(Text, nullable=True)
    contact_email             = Column(String, nullable=True)
    contact_phone             = Column(String, nullable=True)
    classification_confidence = Column(Float, nullable=True)
    sla_deadline              = Column(DateTime(timezone=True), nullable=True)
    opened_at                 = Column(DateTime(timezone=True), nullable=True)
    closed_at                 = Column(DateTime(timezone=True), nullable=True)

    # FKs
    submission_id             = Column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=True
    )
    district_id               = Column(Integer, ForeignKey("districts.id"), nullable=True)
    queue_id                  = Column(Integer, ForeignKey("queues.id"), nullable=True)
    incident_cluster_id       = Column(
        UUID(as_uuid=True), ForeignKey("incident_clusters.id"), nullable=True
    )

    # Relationships
    submission                = relationship("Submission", back_populates="cases")
    district                  = relationship("District", back_populates="cases")
    queue                     = relationship("Queue", back_populates="cases")
    incident_cluster          = relationship("IncidentCluster", back_populates="cases")
    assignments               = relationship("Assignment", back_populates="case")
    audit_events              = relationship(
        "AuditEvent",
        primaryjoin="and_(AuditEvent.object_type=='case', "
                    "cast(AuditEvent.object_id, UUID)==Case.id)",
        foreign_keys="AuditEvent.object_id",
        viewonly=True,
    )
