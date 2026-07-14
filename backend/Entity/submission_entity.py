import uuid
from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import ChannelEnum, ConsentStatusEnum


class Submission(Base, TimestampMixin):
    """
    Raw intake record — one row per channel event.

    This is the canonical intake envelope described in the architecture doc
    (§3). Every submission receives an immutable UUID at the gateway layer
    before any AI processing begins.

    citizen_contact_id is nullable to support anonymous reporting.
    district_id is nullable — resolved asynchronously after intake.
    attachment_refs stores UUIDs of related Document records.
    """
    __tablename__ = "submissions"

    id                        = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    channel                   = Column(String, nullable=False)          # ChannelEnum
    received_at               = Column(DateTime(timezone=True), nullable=False)
    raw_text_ref              = Column(String, nullable=True)           # storage path
    transcript                = Column(Text, nullable=True)
    language_code             = Column(String(10), nullable=True)
    language_confidence       = Column(Float, nullable=True)
    consent_status            = Column(String, nullable=False,
                                       default=ConsentStatusEnum.NOT_REQUIRED)
    citizen_contact_token     = Column(String, nullable=True)           # tokenised
    location_text             = Column(Text, nullable=True)
    service_description       = Column(Text, nullable=False)
    contact_email             = Column(String, nullable=True)
    contact_phone             = Column(String, nullable=True)
    attachment_refs           = Column(JSON, nullable=True, default=list)  # list[UUID str]
    accessibility_preferences = Column(JSON, nullable=True, default=dict)
    source_metadata           = Column(JSON, nullable=False, default=dict)

    # FK — optional PII link
    citizen_contact_id        = Column(
        Integer, ForeignKey("citizen_contacts.id"), nullable=True
    )
    # FK — resolved after intake, may be null initially
    district_id               = Column(
        Integer, ForeignKey("districts.id"), nullable=True
    )
    # FK — authenticated user who submitted (null for anonymous / non-web channels)
    submitter_user_id         = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

    # Relationships
    citizen_contact           = relationship("CitizenContact", back_populates="submissions")
    district                  = relationship("District", back_populates="submissions")
    documents                 = relationship("Document", back_populates="submission")
    cases                     = relationship("Case", back_populates="submission")
    notifications             = relationship("Notification", back_populates="submission")
