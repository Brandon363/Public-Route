from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin


class CitizenContact(Base, TimestampMixin):
    """
    PII-separated citizen identity record (DR-003).

    Contact information is stored here in isolation from all analytical
    and operational case records. The encrypted_phone field stores the
    citizen's identifier as an application-layer tokenised string.
    Anonymous reporting is supported — this table is NOT required to
    exist for every Submission.
    """
    __tablename__ = "citizen_contacts"

    id                        = Column(Integer, primary_key=True, index=True)
    encrypted_phone           = Column(String, nullable=True)   # tokenised/encrypted
    preferred_channel         = Column(String, nullable=True)   # ChannelEnum value
    language_code             = Column(String(10), nullable=True)
    accessibility_preferences = Column(JSON, nullable=True, default=dict)

    # Relationships
    submissions               = relationship("Submission", back_populates="citizen_contact")
    notifications             = relationship("Notification", back_populates="citizen_contact")
