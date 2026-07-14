import uuid
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import SeverityEnum, CaseStatusEnum


class IncidentCluster(Base, TimestampMixin):
    """
    A grouped set of related cases/reports sharing a common root cause,
    geographic cluster or pattern signature.

    Duplicate detection links individual Cases to an IncidentCluster.
    No direct PII is stored here — analytics-safe by design.

    signature: a content hash or embedding fingerprint used for matching.
    geography_json: GeoJSON or {lat, lng, radius_m} bounding area.
    """
    __tablename__ = "incident_clusters"

    id            = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    signature     = Column(String, nullable=True, index=True)
    geography_json = Column(JSON, nullable=True, default=dict)
    category      = Column(String, nullable=False)
    subcategory   = Column(String, nullable=True)
    description   = Column(Text, nullable=True)
    opened_at     = Column(DateTime(timezone=True), nullable=True)
    closed_at     = Column(DateTime(timezone=True), nullable=True)
    status        = Column(
        String, nullable=False, default=CaseStatusEnum.RECEIVED, index=True
    )
    severity      = Column(String, nullable=False, default=SeverityEnum.MEDIUM)

    # Relationships
    cases         = relationship("Case", back_populates="incident_cluster")
    assignments   = relationship("Assignment", back_populates="incident_cluster")
