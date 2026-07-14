from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import AssignmentStatusEnum


class Assignment(Base, TimestampMixin):
    """
    Links a Case or IncidentCluster to a ResourceTeam.

    Either case_id or incident_cluster_id must be set; both can be set
    when a cluster-level assignment covers multiple cases.
    Every assignment change is captured in AuditEvent.
    """
    __tablename__ = "assignments"

    id                  = Column(Integer, primary_key=True, index=True)
    case_id             = Column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True
    )
    incident_cluster_id = Column(
        UUID(as_uuid=True), ForeignKey("incident_clusters.id"), nullable=True
    )
    team_id             = Column(Integer, ForeignKey("resource_teams.id"), nullable=False)
    assigned_at         = Column(DateTime(timezone=True), nullable=True)
    status              = Column(
        String, nullable=False, default=AssignmentStatusEnum.PENDING
    )
    outcome             = Column(Text, nullable=True)
    notes               = Column(Text, nullable=True)

    # Relationships
    case                = relationship("Case", back_populates="assignments")
    incident_cluster    = relationship("IncidentCluster", back_populates="assignments")
    team                = relationship("ResourceTeam", back_populates="assignments")
