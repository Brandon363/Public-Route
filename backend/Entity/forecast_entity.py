from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin


class Forecast(Base, TimestampMixin):
    """
    Demand forecast output produced by an approved forecasting pipeline (FR-014).

    One record per forecast cell (period × geography × category).
    Always linked to the ModelVersion that produced it for full model
    governance traceability (AI-007).

    value: the point estimate of demand for the given cell.
    lower_bound / upper_bound: prediction interval boundaries.
    """
    __tablename__ = "forecasts"

    id               = Column(Integer, primary_key=True, index=True)
    period_start     = Column(DateTime(timezone=True), nullable=False)
    period_end       = Column(DateTime(timezone=True), nullable=False)
    district_id      = Column(Integer, ForeignKey("districts.id"), nullable=True)
    category         = Column(String, nullable=True)
    subcategory      = Column(String, nullable=True)
    value            = Column(Float, nullable=False)
    lower_bound      = Column(Float, nullable=True)
    upper_bound      = Column(Float, nullable=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False)

    # Relationships
    district         = relationship("District", back_populates="forecasts")
    model_version    = relationship("ModelVersion", back_populates="forecasts")
    recommendations  = relationship("Recommendation", back_populates="forecast")
