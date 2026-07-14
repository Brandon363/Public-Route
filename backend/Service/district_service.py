from sqlalchemy.orm import Session
from Repository.district_repository import DistrictRepository
from Schema.district_schema import DistrictCreate, DistrictUpdate
from Entity.district_entity import District
from Utils.Enums import SettlementTypeEnum


class DistrictService:
    """
    Business logic for the District reference data domain.
    No FastAPI imports — raises ValueError for all rule violations.
    """

    def __init__(self, db: Session):
        self.repository = DistrictRepository(db)

    def _validate_settlement_type(self, settlement_type: str) -> None:
        valid = [e.value for e in SettlementTypeEnum]
        if settlement_type not in valid:
            raise ValueError(
                f"Invalid settlement_type '{settlement_type}'. Must be one of: {valid}"
            )

    def create_district(self, data: DistrictCreate) -> District:
        """
        Create a new district.
        Name must be unique within its province.
        """
        self._validate_settlement_type(data.settlement_type)

        existing = self.repository.get_by_name(data.name)
        if existing is not None:
            raise ValueError(f"A district named '{data.name}' already exists.")

        district = District(
            name=data.name,
            province=data.province,
            settlement_type=data.settlement_type,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        return self.repository.create(district)

    def get_district(self, district_id: int) -> District:
        district = self.repository.get_by_id(district_id)
        if district is None:
            raise ValueError(f"District with ID {district_id} not found.")
        return district

    def get_all_districts(self, skip: int = 0, limit: int = 100) -> list[District]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get_districts_by_province(self, province: str) -> list[District]:
        return self.repository.get_by_province(province)

    def update_district(self, district_id: int, data: DistrictUpdate) -> District:
        district = self.repository.get_by_id(district_id)
        if district is None:
            raise ValueError(f"District with ID {district_id} not found.")

        update_data = data.model_dump(exclude_unset=True)

        if "settlement_type" in update_data:
            self._validate_settlement_type(update_data["settlement_type"])

        if "name" in update_data:
            existing = self.repository.get_by_name(update_data["name"])
            if existing is not None and existing.id != district_id:
                raise ValueError(
                    f"A district named '{update_data['name']}' already exists."
                )

        return self.repository.update(district, update_data)

    def delete_district(self, district_id: int) -> None:
        district = self.repository.get_by_id(district_id)
        if district is None:
            raise ValueError(f"District with ID {district_id} not found.")
        self.repository.delete(district)
