from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker
from Schema.queue_schema import QueueCreate, QueueUpdate, QueueResponse
from Service.queue_service import QueueService
from Utils.permissions import CAN_MANAGE_REFERENCE_DATA, CAN_MANAGE_QUEUE
from Entity.user_entity import User

router = APIRouter(prefix="/queues", tags=["Reference — Queues"])

_require_admin = RoleChecker(CAN_MANAGE_REFERENCE_DATA)
_require_queue_manager = RoleChecker(CAN_MANAGE_QUEUE)


@router.post("/", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
def create_queue(
    data: QueueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = QueueService(db)
    try:
        queue = service.create_queue(data)
        return QueueResponse(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="Queue created successfully.",
            queue=queue,
        )
    except ValueError as e:
        return QueueResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return QueueResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/", response_model=QueueResponse, status_code=status.HTTP_200_OK)
def list_queues(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False, description="Return only active queues"),
    unit_id: int | None = Query(None, description="Filter by organisation unit ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QueueService(db)
    try:
        if unit_id is not None:
            queues = service.get_queues_by_unit(unit_id)
        elif active_only:
            queues = service.get_active_queues()
        else:
            queues = service.get_all_queues(skip=skip, limit=limit)
        return QueueResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Queues retrieved successfully.",
            queues=queues,
        )
    except ValueError as e:
        return QueueResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return QueueResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve queues.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/{queue_id}", response_model=QueueResponse, status_code=status.HTTP_200_OK)
def get_queue(
    queue_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QueueService(db)
    try:
        queue = service.get_queue(queue_id)
        return QueueResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Queue retrieved successfully.",
            queue=queue,
        )
    except ValueError as e:
        return QueueResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return QueueResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.put("/{queue_id}", response_model=QueueResponse, status_code=status.HTTP_200_OK)
def update_queue(
    data: QueueUpdate,
    queue_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_queue_manager),
):
    """Supervisors and administrators can update queue configuration."""
    service = QueueService(db)
    try:
        queue = service.update_queue(queue_id, data)
        return QueueResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Queue updated successfully.",
            queue=queue,
        )
    except ValueError as e:
        return QueueResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return QueueResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to update queue.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.patch("/{queue_id}/deactivate", response_model=QueueResponse, status_code=status.HTTP_200_OK)
def deactivate_queue(
    queue_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_queue_manager),
):
    """Soft-deactivate a queue. Preferred over hard delete to preserve case history."""
    service = QueueService(db)
    try:
        queue = service.deactivate_queue(queue_id)
        return QueueResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Queue deactivated.",
            queue=queue,
        )
    except ValueError as e:
        return QueueResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return QueueResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to deactivate queue.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.delete("/{queue_id}", response_model=QueueResponse, status_code=status.HTTP_200_OK)
def delete_queue(
    queue_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    service = QueueService(db)
    try:
        service.delete_queue(queue_id)
        return QueueResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Queue deleted successfully.",
        )
    except ValueError as e:
        return QueueResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return QueueResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to delete queue.",
            errors=[{"field": "general", "message": str(e)}],
        )
