from sqlalchemy.orm import Session
from Repository.user_repository import UserRepository
from Schema.user_schema import UserCreate, UserUpdate
from Utils.security import get_password_hash
from Utils.permissions import ALL_ROLES
from Entity.user_entity import User


class UserService:
    """
    Pure Python service layer for User CRUD operations.
    Contains zero FastAPI imports. Handles all business rule validation
    and raises ValueError for any failure condition.
    """

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def _validate_role(self, role: str) -> None:
        if role not in ALL_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: {ALL_ROLES}"
            )

    def create_new_user(self, user_data: UserCreate) -> User:
        """
        Create a new auth user record.

        Validates that the email is not already registered and that the
        role is a recognised value. Hashes the password before persistence.
        """
        self._validate_role(user_data.role)

        existing = self.repository.get_user_by_email(user_data.email)
        if existing is not None:
            raise ValueError(f"A user with the email '{user_data.email}' already exists.")

        hashed_pw = get_password_hash(user_data.password)

        db_user = User(
            email=user_data.email,
            hashed_password=hashed_pw,
            role=user_data.role,
        )
        return self.repository.create_user(db_user)

    def get_user_by_id(self, user_id: int) -> User:
        db_user = self.repository.get_user_by_id(user_id)
        if db_user is None:
            raise ValueError(f"User with ID {user_id} not found.")
        return db_user

    def get_all_users(self) -> list[User]:
        return self.repository.get_all_users()

    def update_existing_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update an existing user record.

        Validates email uniqueness if the email is being changed.
        Re-hashes the password if a new one is provided.
        """
        db_user = self.repository.get_user_by_id(user_id)
        if db_user is None:
            raise ValueError(f"User with ID {user_id} not found.")

        update_data = user_data.model_dump(exclude_unset=True)

        if "email" in update_data:
            existing = self.repository.get_user_by_email(update_data["email"])
            if existing is not None and existing.id != user_id:
                raise ValueError(
                    f"A user with the email '{update_data['email']}' already exists."
                )

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return self.repository.update_user(db_user, update_data)

    def remove_user(self, user_id: int) -> None:
        db_user = self.repository.get_user_by_id(user_id)
        if db_user is None:
            raise ValueError(f"User with ID {user_id} not found.")
        self.repository.delete_user(db_user)
