from sqlalchemy.orm import Session
from Repository.resource_team_repository import ResourceTeamRepository
from Repository.district_repository import DistrictRepository
from Schema.resource_team_schema import ResourceTeamCreate, ResourceTeamUpdate
from Entity.resource_team_entity import ResourceTeam


class ResourceTeamService:
    """
    Business logic for the ResourceTeam reference data domain.
    No FastAPI imports — raises ValueError for all rule violations.

    When a base_district_id is supplied, the service verifies the district
    exists before creating or updating the team.
    """

    def __init__(self, db: Session):
        self.repository = ResourceTeamRepository(db)
        self.district_repository = DistrictRepository(db)

    def _assert_district_exists(self, district_id: int) -> None:
        if self.district_repository.get_by_id(district_id) is None:
            raise ValueError(f"District with ID {district_id} not found.")

    def create_team(self, data: ResourceTeamCreate) -> ResourceTeam:
        """
        Create a new resource team.
        Team names must be unique. If a base district is supplied it must exist.
        """
        existing = self.repository.get_by_name(data.name)
        if existing is not None:
            raise ValueError(f"A resource team named '{data.name}' already exists.")

        if data.base_district_id is not None:
            self._assert_district_exists(data.base_district_id)

        team = ResourceTeam(
            name=data.name,
            skills=data.skills or [],
            service_categories=data.service_categories or [],
            capacity=data.capacity,
            base_district_id=data.base_district_id,
            availability_schedule=data.availability_schedule or {},
            is_active=data.is_active,
        )
        return self.repository.create(team)

    def get_team(self, team_id: int) -> ResourceTeam:
        team = self.repository.get_by_id(team_id)
        if team is None:
            raise ValueError(f"Resource team with ID {team_id} not found.")
        return team

    def get_all_teams(self, skip: int = 0, limit: int = 100) -> list[ResourceTeam]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get_active_teams(self) -> list[ResourceTeam]:
        return self.repository.get_active()

    def get_teams_by_district(self, district_id: int) -> list[ResourceTeam]:
        self._assert_district_exists(district_id)
        return self.repository.get_by_district(district_id)

    def update_team(self, team_id: int, data: ResourceTeamUpdate) -> ResourceTeam:
        team = self.repository.get_by_id(team_id)
        if team is None:
            raise ValueError(f"Resource team with ID {team_id} not found.")

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = self.repository.get_by_name(update_data["name"])
            if existing is not None and existing.id != team_id:
                raise ValueError(
                    f"A resource team named '{update_data['name']}' already exists."
                )

        if "base_district_id" in update_data and update_data["base_district_id"] is not None:
            self._assert_district_exists(update_data["base_district_id"])

        return self.repository.update(team, update_data)

    def deactivate_team(self, team_id: int) -> ResourceTeam:
        """Soft-delete: marks the team inactive without removing it."""
        team = self.repository.get_by_id(team_id)
        if team is None:
            raise ValueError(f"Resource team with ID {team_id} not found.")
        return self.repository.update(team, {"is_active": False})

    def delete_team(self, team_id: int) -> None:
        team = self.repository.get_by_id(team_id)
        if team is None:
            raise ValueError(f"Resource team with ID {team_id} not found.")
        self.repository.delete(team)
