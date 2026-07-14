from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin


class Queue(Base, TimestampMixin):
    """
    A department's case queue with configurable priority rules and capacity.

    priority_rules: JSON object describing how cases are ordered within
    this queue (e.g. by urgency, SLA deadline, geography).
    """
    __tablename__ = "queues"

    id                  = Column(Integer, primary_key=True, index=True)
    unit_id             = Column(Integer, ForeignKey("organisation_units.id"), nullable=False)
    name                = Column(String, nullable=False)
    priority_rules      = Column(JSON, nullable=True, default=dict)
    capacity            = Column(Integer, nullable=True)
    is_active           = Column(Boolean, default=True, nullable=False)

    # Relationships
    organisation_unit   = relationship("OrganisationUnit", back_populates="queues")
    cases               = relationship("Case", back_populates="queue")
