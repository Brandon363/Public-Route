from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from Config.database import Base, TimestampMixin
from Utils.Enums import ApprovalDecisionEnum


class Approval(Base, TimestampMixin):
    """
    Immutable human decision record for a Recommendation (FR-018).

    Once created, this record must not be modified. Overrides and
    rejected decisions remain permanently visible in the audit trail.
    reviewer_user_id links to the User who made the decision.
    """
    __tablename__ = "approvals"

    id                  = Column(Integer, primary_key=True, index=True)
    recommendation_id   = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    reviewer_user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision            = Column(String, nullable=False)    # ApprovalDecisionEnum
    reason              = Column(Text, nullable=False)
    decided_at          = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    recommendation      = relationship("Recommendation", back_populates="approvals")
    reviewer            = relationship("User")
