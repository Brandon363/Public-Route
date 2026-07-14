from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker
from Schema.user_schema import UserCreate, UserUpdate, UserResponse
from Service.user_service import UserService
from Utils.permissions import CAN_MANAGE_USERS
from Entity.user_entity import User

router = APIRouter(prefix="/users", tags=["Users"])

_require_manager = RoleChecker(CAN_MANAGE_USERS)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager)
):
    service = UserService(db)
    try:
        new_user = service.create_new_user(user_data)
        return UserResponse(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="User created successfully.",
            user=new_user
        )
    except ValueError as e:
        return UserResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}]
        )
    except Exception as e:
        return UserResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}]
        )


@router.get("/", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager)
):
    service = UserService(db)
    try:
        users = service.get_all_users()
        return UserResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Users retrieved successfully.",
            users=users
        )
    except Exception as e:
        return UserResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve users.",
            errors=[{"field": "general", "message": str(e)}]
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Return the profile of the currently authenticated caller."""
    return UserResponse(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Current user retrieved successfully.",
        user=current_user
    )


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager)
):
    service = UserService(db)
    try:
        user = service.get_user_by_id(user_id)
        return UserResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User retrieved successfully.",
            user=user
        )
    except ValueError as e:
        return UserResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}]
        )
    except Exception as e:
        return UserResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}]
        )


@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user(
    user_data: UserUpdate,
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager)
):
    service = UserService(db)
    try:
        updated_user = service.update_existing_user(user_id, user_data)
        return UserResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User updated successfully.",
            user=updated_user
        )
    except ValueError as e:
        return UserResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}]
        )
    except Exception as e:
        return UserResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to update user.",
            errors=[{"field": "general", "message": str(e)}]
        )


@router.delete("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager)
):
    service = UserService(db)
    try:
        service.remove_user(user_id)
        return UserResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="User deleted successfully."
        )
    except ValueError as e:
        return UserResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}]
        )
    except Exception as e:
        return UserResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to delete user.",
            errors=[{"field": "general", "message": str(e)}]
        )
