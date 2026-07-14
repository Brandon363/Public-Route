from sqlalchemy.orm import Session
from Entity.organisation_unit_entity import OrganisationUnit


class OrganisationUnitRepository:
    """
    Data access layer for the OrganisationUnit reference table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, unit_id: int) -> OrganisationUnit | None:
        return self.db.query(OrganisationUnit).filter(OrganisationUnit.id == unit_id).first()

    def get_by_name(self, name: str) -> OrganisationUnit | None:
        return self.db.query(OrganisationUnit).filter(OrganisationUnit.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[OrganisationUnit]:
        return self.db.query(OrganisationUnit).offset(skip).limit(limit).all()

    def get_active(self) -> list[OrganisationUnit]:
        return (
            self.db.query(OrganisationUnit)
            .filter(OrganisationUnit.is_active == True)  # noqa: E712
            .all()
        )

    def create(self, unit: OrganisationUnit) -> OrganisationUnit:
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        return unit

    def update(self, unit: OrganisationUnit, update_data: dict) -> OrganisationUnit:
        for key, value in update_data.items():
            setattr(unit, key, value)
        self.db.commit()
        self.db.refresh(unit)
        return unit

    def delete(self, unit: OrganisationUnit) -> None:
        self.db.delete(unit)
        self.db.commit()
