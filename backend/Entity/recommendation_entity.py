from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import RecommendationStatusEnum


class Recommendation(Base, TimestampMixin):
    """
    AI-generated action plan requiring human approval before implementation (FR-017, FR-018).

    Recommendation records are immutable once status reaches APPROVED or REJECTED.
    Every field provides the approval reviewer with full context:
    - action_description: what the system recommends doing.
    - expected_impact: modelled outcome if the action is taken.
    - rationale: key drivers and explanation behind the recommendation.
    - assumptions: listed constraints and inputs used by the optimiser.
    """
    __tablename__ = "recommendations"

    id                  = Column(Integer, primary_key=True, index=True)
    scenario_label      = Column(String, nullable=False)
    action_description  = Column(Text, nullable=False)
    expected_impact     = Column(Text, nullable=True)
    rationale           = Column(Text, nullable=True)
    assumptions         = Column(Text, nullable=True)
    status              = Column(
        String, nullable=False, default=RecommendationStatusEnum.DRAFT, index=True
    )
    forecast_id         = Column(Integer, ForeignKey("forecasts.id"), nullable=True)
    model_version_id    = Column(Integer, ForeignKey("model_versions.id"), nullable=True)

    # Relationships
    forecast            = relationship("Forecast", back_populates="recommendations")
    model_version       = relationship("ModelVersion", back_populates="recommendations")
    approvals           = relationship("Approval", back_populates="recommendation")
