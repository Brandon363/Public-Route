from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from Config.database import get_db, SECRET_KEY, ALGORITHM
from Entity.user_entity import User


# The token URL must match the login endpoint path registered in auth_controller.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that authenticates the caller on every protected request.

    Decodes the bearer token, verifies the payload claims, fetches the user
    record, and critically performs a token version check. If the token's
    embedded version does not match the database record, the token is
    considered revoked and a 401 is raised immediately. This is the
    kill-switch for instant global logout without a blacklist table.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        token_version: int = payload.get("token_version")

        if email is None or role is None or token_version is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    db_user = db.query(User).filter(User.email == email).first()

    if db_user is None:
        raise credentials_exception

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token version check: if the counter in the token does not match the
    # current database value, the token has been revoked via the kill-switch.
    if token_version != db_user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return db_user


class RoleChecker:
    """
    Callable FastAPI dependency class that enforces role-based access control.

    Usage in a controller:
        from Utils.permissions import CAN_MANAGE_USERS
        from Config.dependencies import RoleChecker, get_current_user

        require_manager = RoleChecker(CAN_MANAGE_USERS)

        @router.post("/", dependencies=[Depends(require_manager)])
        def create_something(..., current_user: User = Depends(get_current_user)):
            ...

    Alternatively the RoleChecker can be declared inline:
        @router.post("/", dependencies=[Depends(RoleChecker(CAN_MANAGE_USERS))])
    """

    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user


from fastapi import Request
from typing import Optional

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication helper: decodes Bearer token if present,
    but returns None instead of raising a 401 if missing or invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return db.query(User).filter(User.email == email).first()
    except Exception:
        return None
