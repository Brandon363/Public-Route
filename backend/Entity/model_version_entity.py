from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import ModelStatusEnum


class ModelVersion(Base, TimestampMixin):
    """
    AI model governance record — one row per trained and versioned model.

    Satisfies AI-007: version models, feature schemas, thresholds and deployments.
    Every Forecast and Prediction links back to the exact model version that
    produced it, enabling full audit and model risk review (FR-022).

    purpose: human-readable label (e.g. "service_classifier", "demand_forecast").
    feature_schema: JSON list/dict describing the input features.
    metrics: JSON object with evaluation scores (MAE, RMSE, accuracy, etc.).
    training_data_ref: reference string or URI to the dataset version used.
    """
    __tablename__ = "model_versions"

    id                 = Column(Integer, primary_key=True, index=True)
    purpose            = Column(String, nullable=False, index=True)
    version_tag        = Column(String, nullable=False)    # e.g. "v1.2.0"
    feature_schema     = Column(JSON, nullable=True, default=dict)
    metrics            = Column(JSON, nullable=True, default=dict)
    threshold          = Column(Float, nullable=True)
    training_data_ref  = Column(Text, nullable=True)
    status             = Column(
        String, nullable=False, default=ModelStatusEnum.TRAINING, index=True
    )
    deployed_at        = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    forecasts          = relationship("Forecast", back_populates="model_version")
    recommendations    = relationship("Recommendation", back_populates="model_version")
