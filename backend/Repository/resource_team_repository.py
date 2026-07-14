from sqlalchemy.orm import Session
from Entity.resource_team_entity import ResourceTeam


class ResourceTeamRepository:
    """
    Data access layer for the ResourceTeam reference table.
    Zero business logic — all validation is handled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, team_id: int) -> ResourceTeam | None:
        return self.db.query(ResourceTeam).filter(ResourceTeam.id == team_id).first()

    def get_by_name(self, name: str) -> ResourceTeam | None:
        return self.db.query(ResourceTeam).filter(ResourceTeam.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[ResourceTeam]:
        return self.db.query(ResourceTeam).offset(skip).limit(limit).all()

    def get_active(self) -> list[ResourceTeam]:
        return (
            self.db.query(ResourceTeam)
            .filter(ResourceTeam.is_active == True)  # noqa: E712
            .all()
        )

    def get_by_district(self, district_id: int) -> list[ResourceTeam]:
        return (
            self.db.query(ResourceTeam)
            .filter(ResourceTeam.base_district_id == district_id)
            .all()
        )

    def create(self, team: ResourceTeam) -> ResourceTeam:
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def update(self, team: ResourceTeam, update_data: dict) -> ResourceTeam:
        for key, value in update_data.items():
            setattr(team, key, value)
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete(self, team: ResourceTeam) -> None:
        self.db.delete(team)
        self.db.commit()
