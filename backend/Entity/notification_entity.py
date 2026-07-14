from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import ChannelEnum, DeliveryStatusEnum


class Notification(Base, TimestampMixin):
    """
    Outbound status notification sent to a citizen via their preferred channel.

    Linked to a Submission (provides submission context) and optionally to
    a CitizenContact (for PII-controlled delivery metadata). Delivery receipts,
    retries and opt-outs are tracked here per FR-012.
    """
    __tablename__ = "notifications"

    id                  = Column(Integer, primary_key=True, index=True)
    submission_id       = Column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=True
    )
    citizen_contact_id  = Column(
        Integer, ForeignKey("citizen_contacts.id"), nullable=True
    )
    channel             = Column(String, nullable=False)    # ChannelEnum
    message             = Column(Text, nullable=False)
    delivery_status     = Column(
        String, nullable=False, default=DeliveryStatusEnum.QUEUED
    )
    sent_at             = Column(DateTime(timezone=True), nullable=True)
    delivered_at        = Column(DateTime(timezone=True), nullable=True)
    failure_reason      = Column(Text, nullable=True)

    # Relationships
    submission          = relationship("Submission", back_populates="notifications")
    citizen_contact     = relationship("CitizenContact", back_populates="notifications")
