from fastapi import APIRouter, Depends, status, Path
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker
from Schema.user_schema import TokenResponse, UserDTO, UserResponse
from Service.auth_service import AuthService
from Utils.security import create_access_token
from Utils.permissions import CAN_MANAGE_USERS
from Entity.user_entity import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Instantiate the role checker once and reuse across protected routes.
_require_manager = RoleChecker(CAN_MANAGE_USERS)


@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2-compatible login endpoint.

    Accepts form fields 'username' (used as email) and 'password'.
    Returns the raw access_token and token_type structure required by the
    FastAPI Swagger UI 'Authorize' button. This endpoint is intentionally
    NOT wrapped in BaseResponse to maintain OAuth2 compatibility.
    """
    service = AuthService(db)
    try:
        db_user = service.authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": db_user.email,
        "role": db_user.role,
        "token_version": db_user.token_version,
    }
    access_token = create_access_token(data=token_data)

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/revoke/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def revoke_user_tokens(
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_manager)
):
    """
    Increment the target user's token_version counter.

    All JWTs previously issued to that user are immediately invalidated.
    This provides an instant global logout kill-switch without a blacklist table.
    Restricted to users with roles in CAN_MANAGE_USERS.
    """
    service = AuthService(db)
    try:
        updated_user = service.revoke_user_tokens(user_id)
        return UserResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message=f"All tokens for user ID {user_id} have been revoked.",
            user=updated_user
        )
    except ValueError as e:
        return UserResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "user_id", "message": str(e)}]
        )
    except Exception as e:
        return UserResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}]
        )
