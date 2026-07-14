from sqlalchemy.orm import Session
from Repository.user_repository import UserRepository
from Utils.security import verify_password
from Entity.user_entity import User


class AuthService:
    """
    Pure Python service layer for authentication operations.
    Contains zero FastAPI imports. All failures are raised as ValueError
    so the controller layer can translate them into HTTP responses.
    """

    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def authenticate_user(self, email: str, password: str) -> User:
        """
        Verify the provided credentials against the database.

        Raises ValueError if:
          - No user exists with the given email.
          - The password does not match the stored hash.
          - The account has been deactivated.

        Returns the User entity on success.
        """
        db_user = self.user_repository.get_user_by_email(email)

        # Use a generic message for both missing user and wrong password
        # to avoid leaking whether an email address is registered.
        if db_user is None or not verify_password(password, db_user.hashed_password):
            raise ValueError("Invalid email address or password.")

        if not db_user.is_active:
            raise ValueError("This account has been deactivated.")

        return db_user

    def revoke_user_tokens(self, user_id: int) -> User:
        """
        Increment the token_version counter for the given user.
        All JWTs issued before this call are immediately invalidated.
        """
        db_user = self.user_repository.get_user_by_id(user_id)
        if db_user is None:
            raise ValueError(f"User with ID {user_id} not found.")

        return self.user_repository.increment_token_version(db_user)
