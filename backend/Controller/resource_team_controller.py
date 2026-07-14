from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker
from Schema.resource_team_schema import ResourceTeamCreate, ResourceTeamUpdate, ResourceTeamResponse
from Service.resource_team_service import ResourceTeamService
from Utils.permissions import CAN_MANAGE_REFERENCE_DATA, CAN_MANAGE_QUEUE
from Entity.user_entity import User

router = APIRouter(prefix="/resource-teams", tags=["Reference — Resource Teams"])

_require_admin = RoleChecker(CAN_MANAGE_REFERENCE_DATA)
_require_supervisor = RoleChecker(CAN_MANAGE_QUEUE)


@router.post("/", response_model=ResourceTeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    data: ResourceTeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = ResourceTeamService(db)
    try:
        team = service.create_team(data)
        return ResourceTeamResponse(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="Resource team created successfully.",
            team=team,
        )
    except ValueError as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/", response_model=ResourceTeamResponse, status_code=status.HTTP_200_OK)
def list_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False, description="Return only active teams"),
    district_id: int | None = Query(None, description="Filter by base district ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResourceTeamService(db)
    try:
        if district_id is not None:
            teams = service.get_teams_by_district(district_id)
        elif active_only:
            teams = service.get_active_teams()
        else:
            teams = service.get_all_teams(skip=skip, limit=limit)
        return ResourceTeamResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Resource teams retrieved successfully.",
            teams=teams,
        )
    except ValueError as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve resource teams.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/{team_id}", response_model=ResourceTeamResponse, status_code=status.HTTP_200_OK)
def get_team(
    team_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResourceTeamService(db)
    try:
        team = service.get_team(team_id)
        return ResourceTeamResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Resource team retrieved successfully.",
            team=team,
        )
    except ValueError as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.put("/{team_id}", response_model=ResourceTeamResponse, status_code=status.HTTP_200_OK)
def update_team(
    data: ResourceTeamUpdate,
    team_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_supervisor),
):
    """Supervisors and administrators can update team configuration."""
    service = ResourceTeamService(db)
    try:
        team = service.update_team(team_id, data)
        return ResourceTeamResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Resource team updated successfully.",
            team=team,
        )
    except ValueError as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to update resource team.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.patch("/{team_id}/deactivate", response_model=ResourceTeamResponse, status_code=status.HTTP_200_OK)
def deactivate_team(
    team_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_supervisor),
):
    """Soft-deactivate a team without removing assignment history."""
    service = ResourceTeamService(db)
    try:
        team = service.deactivate_team(team_id)
        return ResourceTeamResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Resource team deactivated.",
            team=team,
        )
    except ValueError as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to deactivate team.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.delete("/{team_id}", response_model=ResourceTeamResponse, status_code=status.HTTP_200_OK)
def delete_team(
    team_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = ResourceTeamService(db)
    try:
        service.delete_team(team_id)
        return ResourceTeamResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Resource team deleted successfully.",
        )
    except ValueError as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return ResourceTeamResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to delete resource team.",
            errors=[{"field": "general", "message": str(e)}],
        )
