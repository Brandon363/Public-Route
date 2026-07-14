from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin


class OrganisationUnit(Base, TimestampMixin):
    """
    A government department or service unit that owns queues and handles cases.

    jurisdiction: JSON list of district IDs or province codes this unit covers.
    service_categories: JSON list of service category strings this unit handles.
    escalation_path: JSON list of unit_ids defining the escalation chain.
    """
    __tablename__ = "organisation_units"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String, nullable=False)
    jurisdiction        = Column(JSON, nullable=False, default=list)
    service_categories  = Column(JSON, nullable=False, default=list)
    escalation_path     = Column(JSON, nullable=True, default=list)
    is_active           = Column(Boolean, default=True, nullable=False)

    # Relationships
    queues              = relationship("Queue", back_populates="organisation_unit")
