from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker
from Schema.organisation_unit_schema import (
    OrganisationUnitCreate,
    OrganisationUnitUpdate,
    OrganisationUnitResponse,
)
from Service.organisation_unit_service import OrganisationUnitService
from Utils.permissions import CAN_MANAGE_REFERENCE_DATA
from Entity.user_entity import User

router = APIRouter(prefix="/organisation-units", tags=["Reference — Organisation Units"])

_require_admin = RoleChecker(CAN_MANAGE_REFERENCE_DATA)


@router.post("/", response_model=OrganisationUnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(
    data: OrganisationUnitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = OrganisationUnitService(db)
    try:
        unit = service.create_unit(data)
        return OrganisationUnitResponse(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="Organisation unit created successfully.",
            unit=unit,
        )
    except ValueError as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/", response_model=OrganisationUnitResponse, status_code=status.HTTP_200_OK)
def list_units(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False, description="Return only active units"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OrganisationUnitService(db)
    try:
        units = (
            service.get_active_units()
            if active_only
            else service.get_all_units(skip=skip, limit=limit)
        )
        return OrganisationUnitResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Organisation units retrieved successfully.",
            units=units,
        )
    except Exception as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve organisation units.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/{unit_id}", response_model=OrganisationUnitResponse, status_code=status.HTTP_200_OK)
def get_unit(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = OrganisationUnitService(db)
    try:
        unit = service.get_unit(unit_id)
        return OrganisationUnitResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Organisation unit retrieved successfully.",
            unit=unit,
        )
    except ValueError as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.put("/{unit_id}", response_model=OrganisationUnitResponse, status_code=status.HTTP_200_OK)
def update_unit(
    data: OrganisationUnitUpdate,
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = OrganisationUnitService(db)
    try:
        unit = service.update_unit(unit_id, data)
        return OrganisationUnitResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Organisation unit updated successfully.",
            unit=unit,
        )
    except ValueError as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to update organisation unit.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.patch(
    "/{unit_id}/deactivate",
    response_model=OrganisationUnitResponse,
    status_code=status.HTTP_200_OK,
)
def deactivate_unit(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    """Soft-deactivate a unit without deleting it."""
    service = OrganisationUnitService(db)
    try:
        unit = service.deactivate_unit(unit_id)
        return OrganisationUnitResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Organisation unit deactivated.",
            unit=unit,
        )
    except ValueError as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to deactivate unit.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.delete("/{unit_id}", response_model=OrganisationUnitResponse, status_code=status.HTTP_200_OK)
def delete_unit(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = OrganisationUnitService(db)
    try:
        service.delete_unit(unit_id)
        return OrganisationUnitResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Organisation unit deleted successfully.",
        )
    except ValueError as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return OrganisationUnitResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to delete organisation unit.",
            errors=[{"field": "general", "message": str(e)}],
        )
