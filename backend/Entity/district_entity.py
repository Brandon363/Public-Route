from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import SettlementTypeEnum


class District(Base, TimestampMixin):
    """
    Administrative geography reference record.

    Used to resolve citizen-reported locations to a canonical district,
    drive routing rules, and enable geographic equity analysis.
    """
    __tablename__ = "districts"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False, index=True)
    province        = Column(String, nullable=False)
    settlement_type = Column(String, nullable=False, default=SettlementTypeEnum.URBAN)
    latitude        = Column(Float, nullable=True)
    longitude       = Column(Float, nullable=True)

    # Relationships
    submissions     = relationship("Submission", back_populates="district")
    cases           = relationship("Case", back_populates="district")
    resource_teams  = relationship("ResourceTeam", back_populates="base_district")
    forecasts       = relationship("Forecast", back_populates="district")
