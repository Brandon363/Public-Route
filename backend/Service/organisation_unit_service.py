from sqlalchemy.orm import Session
from Repository.organisation_unit_repository import OrganisationUnitRepository
from Schema.organisation_unit_schema import OrganisationUnitCreate, OrganisationUnitUpdate
from Entity.organisation_unit_entity import OrganisationUnit


class OrganisationUnitService:
    """
    Business logic for the OrganisationUnit reference data domain.
    No FastAPI imports — raises ValueError for all rule violations.
    """

    def __init__(self, db: Session):
        self.repository = OrganisationUnitRepository(db)

    def create_unit(self, data: OrganisationUnitCreate) -> OrganisationUnit:
        """
        Create a new organisation unit.
        Unit names must be unique across the platform.
        """
        existing = self.repository.get_by_name(data.name)
        if existing is not None:
            raise ValueError(
                f"An organisation unit named '{data.name}' already exists."
            )

        unit = OrganisationUnit(
            name=data.name,
            jurisdiction=data.jurisdiction,
            service_categories=data.service_categories,
            escalation_path=data.escalation_path or [],
            is_active=data.is_active,
        )
        return self.repository.create(unit)

    def get_unit(self, unit_id: int) -> OrganisationUnit:
        unit = self.repository.get_by_id(unit_id)
        if unit is None:
            raise ValueError(f"Organisation unit with ID {unit_id} not found.")
        return unit

    def get_all_units(self, skip: int = 0, limit: int = 100) -> list[OrganisationUnit]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get_active_units(self) -> list[OrganisationUnit]:
        return self.repository.get_active()

    def update_unit(self, unit_id: int, data: OrganisationUnitUpdate) -> OrganisationUnit:
        unit = self.repository.get_by_id(unit_id)
        if unit is None:
            raise ValueError(f"Organisation unit with ID {unit_id} not found.")

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = self.repository.get_by_name(update_data["name"])
            if existing is not None and existing.id != unit_id:
                raise ValueError(
                    f"An organisation unit named '{update_data['name']}' already exists."
                )

        return self.repository.update(unit, update_data)

    def deactivate_unit(self, unit_id: int) -> OrganisationUnit:
        """Soft-delete: marks unit inactive without removing it from the DB."""
        unit = self.repository.get_by_id(unit_id)
        if unit is None:
            raise ValueError(f"Organisation unit with ID {unit_id} not found.")
        return self.repository.update(unit, {"is_active": False})

    def delete_unit(self, unit_id: int) -> None:
        """
        Hard delete. Prefer deactivate_unit() in production — only use
        delete for data cleanup or test teardown.
        """
        unit = self.repository.get_by_id(unit_id)
        if unit is None:
            raise ValueError(f"Organisation unit with ID {unit_id} not found.")
        self.repository.delete(unit)
