from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session
from Entity.case_entity import Case


class CaseRepository:
    """
    Data access layer for the Case (operational case record) table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, case_id: UUID) -> Case | None:
        return self.db.query(Case).filter(Case.id == case_id).first()

    def get_by_reference_number(self, reference_number: str) -> Case | None:
        return (
            self.db.query(Case)
            .filter(Case.reference_number == reference_number)
            .first()
        )

    def count_by_reference_prefix(self, prefix: str) -> int:
        return (
            self.db.query(Case)
            .filter(Case.reference_number.like(f"{prefix}%"))
            .count()
        )

    def get_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        district_id: int | None = None,
        queue_id: int | None = None,
        category: str | None = None,
    ) -> list[Case]:
        query = self._filtered(status, district_id, queue_id, category)
        return (
            query.order_by(Case.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_filtered_for_citizen(
        self,
        submitter_user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        category: str | None = None,
    ) -> list[Case]:
        """Return only the cases whose originating submission was created by this user."""
        from Entity.submission_entity import Submission  # local import avoids circular
        query = (
            self.db.query(Case)
            .join(Submission, Case.submission_id == Submission.id)
            .filter(Submission.submitter_user_id == submitter_user_id)
        )
        if status is not None:
            query = query.filter(Case.status == status)
        if category is not None:
            query = query.filter(Case.category == category)
        return (
            query.order_by(Case.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_group(
        self,
        group_by: str,
        status: str | None = None,
        district_id: int | None = None,
        queue_id: int | None = None,
        category: str | None = None,
    ) -> list[tuple]:
        column = getattr(Case, group_by)
        query = self._filtered(status, district_id, queue_id, category)
        return (
            query.with_entities(column, func.count(Case.id))
            .group_by(column)
            .all()
        )

    def _filtered(
        self,
        status: str | None,
        district_id: int | None,
        queue_id: int | None,
        category: str | None,
    ):
        query = self.db.query(Case)
        if status is not None:
            query = query.filter(Case.status == status)
        if district_id is not None:
            query = query.filter(Case.district_id == district_id)
        if queue_id is not None:
            query = query.filter(Case.queue_id == queue_id)
        if category is not None:
            query = query.filter(Case.category == category)
        return query

    def create(self, case: Case) -> Case:
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def update(self, case: Case, update_data: dict) -> Case:
        for key, value in update_data.items():
            setattr(case, key, value)
        self.db.commit()
        self.db.refresh(case)
        return case
