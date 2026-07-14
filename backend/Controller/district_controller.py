from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker
from Schema.district_schema import DistrictCreate, DistrictUpdate, DistrictResponse
from Service.district_service import DistrictService
from Utils.permissions import CAN_MANAGE_REFERENCE_DATA
from Entity.user_entity import User

router = APIRouter(prefix="/districts", tags=["Reference — Districts"])

_require_admin = RoleChecker(CAN_MANAGE_REFERENCE_DATA)


@router.post("/", response_model=DistrictResponse, status_code=status.HTTP_201_CREATED)
def create_district(
    data: DistrictCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = DistrictService(db)
    try:
        district = service.create_district(data)
        return DistrictResponse(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="District created successfully.",
            district=district,
        )
    except ValueError as e:
        return DistrictResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return DistrictResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/", response_model=DistrictResponse, status_code=status.HTTP_200_OK)
def list_districts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    province: str | None = Query(None, description="Filter by province name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all districts. Optionally filter by province. Accessible to all authenticated users."""
    service = DistrictService(db)
    try:
        if province:
            districts = service.get_districts_by_province(province)
        else:
            districts = service.get_all_districts(skip=skip, limit=limit)
        return DistrictResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Districts retrieved successfully.",
            districts=districts,
        )
    except Exception as e:
        return DistrictResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve districts.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/{district_id}", response_model=DistrictResponse, status_code=status.HTTP_200_OK)
def get_district(
    district_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DistrictService(db)
    try:
        district = service.get_district(district_id)
        return DistrictResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="District retrieved successfully.",
            district=district,
        )
    except ValueError as e:
        return DistrictResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return DistrictResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.put("/{district_id}", response_model=DistrictResponse, status_code=status.HTTP_200_OK)
def update_district(
    data: DistrictUpdate,
    district_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = DistrictService(db)
    try:
        district = service.update_district(district_id, data)
        return DistrictResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="District updated successfully.",
            district=district,
        )
    except ValueError as e:
        return DistrictResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return DistrictResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to update district.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.delete("/{district_id}", response_model=DistrictResponse, status_code=status.HTTP_200_OK)
def delete_district(
    district_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = DistrictService(db)
    try:
        service.delete_district(district_id)
        return DistrictResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="District deleted successfully.",
        )
    except ValueError as e:
        return DistrictResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return DistrictResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to delete district.",
            errors=[{"field": "general", "message": str(e)}],
        )
