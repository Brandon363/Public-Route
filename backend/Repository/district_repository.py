from sqlalchemy.orm import Session
from Entity.district_entity import District


class DistrictRepository:
    """
    Data access layer for the District reference table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, district_id: int) -> District | None:
        return self.db.query(District).filter(District.id == district_id).first()

    def get_by_name(self, name: str) -> District | None:
        return self.db.query(District).filter(District.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[District]:
        return self.db.query(District).offset(skip).limit(limit).all()

    def get_by_province(self, province: str) -> list[District]:
        return (
            self.db.query(District)
            .filter(District.province == province)
            .all()
        )

    def create(self, district: District) -> District:
        self.db.add(district)
        self.db.commit()
        self.db.refresh(district)
        return district

    def update(self, district: District, update_data: dict) -> District:
        for key, value in update_data.items():
            setattr(district, key, value)
        self.db.commit()
        self.db.refresh(district)
        return district

    def delete(self, district: District) -> None:
        self.db.delete(district)
        self.db.commit()
