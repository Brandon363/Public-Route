from uuid import UUID
from sqlalchemy.orm import Session
from Entity.submission_entity import Submission


class SubmissionRepository:
    """
    Data access layer for the Submission (intake envelope) table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, submission_id: UUID) -> Submission | None:
        return self.db.query(Submission).filter(Submission.id == submission_id).first()

    def get_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        channel: str | None = None,
    ) -> list[Submission]:
        query = self.db.query(Submission)
        if channel is not None:
            query = query.filter(Submission.channel == channel)
        return (
            query.order_by(Submission.received_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, submission: Submission) -> Submission:
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def update(self, submission: Submission, update_data: dict) -> Submission:
        for key, value in update_data.items():
            setattr(submission, key, value)
        self.db.commit()
        self.db.refresh(submission)
        return submission
