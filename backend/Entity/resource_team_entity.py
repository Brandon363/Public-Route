from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin


class ResourceTeam(Base, TimestampMixin):
    """
    A field team unit used in assignment and resource optimisation.

    skills: JSON list of skill tags (e.g. ["plumbing", "electrical"]).
    service_categories: JSON list of service types this team can handle.
    availability_schedule: JSON object describing working hours/shifts.
    """
    __tablename__ = "resource_teams"

    id                    = Column(Integer, primary_key=True, index=True)
    name                  = Column(String, nullable=False)
    skills                = Column(JSON, nullable=True, default=list)
    service_categories    = Column(JSON, nullable=True, default=list)
    capacity              = Column(Integer, nullable=False, default=1)
    base_district_id      = Column(Integer, ForeignKey("districts.id"), nullable=True)
    availability_schedule = Column(JSON, nullable=True, default=dict)
    is_active             = Column(Boolean, default=True, nullable=False)

    # Relationships
    base_district         = relationship("District", back_populates="resource_teams")
    assignments           = relationship("Assignment", back_populates="team")
