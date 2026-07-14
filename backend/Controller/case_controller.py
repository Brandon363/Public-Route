from uuid import UUID
from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker
from Schema.case_schema import (
    CaseResponse,
    CaseSummaryResponse,
    ClassificationCorrection,
    RouteCaseRequest,
    CaseStatusUpdate,
)
from Service.case_service import CaseService
from Utils.permissions import CAN_VIEW_CASES, CAN_VIEW_ANALYTICS, CAN_PROCESS_INTAKE, CAN_ROUTE_CASES, ROLE_CITIZEN
from Entity.user_entity import User

router = APIRouter(prefix="/cases", tags=["Cases"])

_require_viewer   = RoleChecker(CAN_VIEW_CASES)
_require_citizen  = RoleChecker([ROLE_CITIZEN])
_require_analyst  = RoleChecker(CAN_VIEW_ANALYTICS)
_require_intake_officer = RoleChecker(CAN_PROCESS_INTAKE)
_require_dispatcher     = RoleChecker(CAN_ROUTE_CASES)


# NOTE: /summary and /mine must be registered before /{case_id} — Starlette
# matches literal path segments in declaration order, so a later /summary
# or /mine route would otherwise be swallowed as a {case_id} path param.
@router.get("/mine", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def list_my_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_citizen),
):
    """Returns only the cases submitted by the currently authenticated citizen."""
    service = CaseService(db)
    try:
        cases = service.list_my_cases(
            submitter_user_id=current_user.id,
            skip=skip, limit=limit, status=status_filter, category=category,
        )
        return CaseResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Your cases retrieved successfully.",
            cases=cases,
        )
    except Exception as e:
        return CaseResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve your cases.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/summary", response_model=CaseSummaryResponse, status_code=status.HTTP_200_OK)
def get_case_summary(
    group_by: str = Query("status", description="One of: status, category, district_id, queue_id"),
    status_filter: str | None = Query(None, alias="status"),
    district_id: int | None = Query(None),
    queue_id: int | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_analyst),
):
    service = CaseService(db)
    try:
        counts = service.get_case_summary(
            group_by=group_by, status=status_filter,
            district_id=district_id, queue_id=queue_id, category=category,
        )
        return CaseSummaryResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Case summary retrieved successfully.",
            counts=counts,
        )
    except ValueError as e:
        return CaseSummaryResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "group_by", "message": str(e)}],
        )
    except Exception as e:
        return CaseSummaryResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve case summary.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: str | None = Query(None, alias="status"),
    district_id: int | None = Query(None),
    queue_id: int | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_viewer),
):
    service = CaseService(db)
    try:
        cases = service.list_cases(
            skip=skip, limit=limit, status=status_filter,
            district_id=district_id, queue_id=queue_id, category=category,
        )
        return CaseResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Cases retrieved successfully.",
            cases=cases,
        )
    except Exception as e:
        return CaseResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve cases.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/{case_id}", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def get_case(
    case_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Staff roles (CAN_VIEW_CASES) may view any case. A citizen may view a case
    only if it originated from a submission they made themselves — checked
    here rather than via RoleChecker because ownership can't be expressed as
    a static role list; it depends on the fetched row. An unauthorised
    citizen gets the same "not found" response as a genuinely missing case
    (rather than a 403) so case existence isn't leaked to non-owners.
    """
    service = CaseService(db)
    try:
        case = service.get_case(case_id)

        is_staff_viewer = current_user.role in CAN_VIEW_CASES
        is_owner = (
            current_user.role == ROLE_CITIZEN
            and CaseService.is_owned_by_citizen(case, current_user.id)
        )
        if not (is_staff_viewer or is_owner):
            raise ValueError(f"Case with ID {case_id} not found.")

        return CaseResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Case retrieved successfully.",
            case=case,
        )
    except ValueError as e:
        return CaseResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return CaseResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.patch("/{case_id}/classification", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def correct_classification(
    data: ClassificationCorrection,
    case_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_intake_officer),
):
    """Officer correction of an AI-suggested classification (FR-008)."""
    service = CaseService(db)
    try:
        case = service.correct_classification(
            case_id, data.category, data.subcategory, data.urgency.value,
            actor_user_id=current_user.id,
        )
        return CaseResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Classification corrected.",
            case=case,
        )
    except ValueError as e:
        return CaseResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return CaseResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to correct classification.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.post("/{case_id}/route", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def route_case(
    data: RouteCaseRequest,
    case_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_dispatcher),
):
    """Dispatcher confirms or overrides the recommended queue (FR-009)."""
    service = CaseService(db)
    try:
        case = service.route_case(case_id, data.queue_id, actor_user_id=current_user.id)
        return CaseResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Case routed.",
            case=case,
        )
    except ValueError as e:
        return CaseResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return CaseResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to route case.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.patch("/{case_id}/status", response_model=CaseResponse, status_code=status.HTTP_200_OK)
def update_case_status(
    data: CaseStatusUpdate,
    case_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_dispatcher),
):
    """Lifecycle transition enforced against the Case state machine (FR-011)."""
    service = CaseService(db)
    try:
        case = service.update_status(
            case_id, data.status.value, data.reason, actor_user_id=current_user.id,
        )
        return CaseResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Case status updated.",
            case=case,
        )
    except ValueError as e:
        return CaseResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "status", "message": str(e)}],
        )
    except Exception as e:
        return CaseResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to update case status.",
            errors=[{"field": "general", "message": str(e)}],
        )
