from sqlalchemy.orm import Session
from Entity.user_entity import User


class UserRepository:
    """
    Dumb data access layer for the User auth table.
    Contains zero business logic. All data is expected to be fully prepared
    by the service layer before being passed to these methods.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_all_users(self) -> list[User]:
        return self.db.query(User).all()

    def create_user(self, db_user: User) -> User:
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user(self, db_user: User, update_data: dict) -> User:
        for key, value in update_data.items():
            setattr(db_user, key, value)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete_user(self, db_user: User) -> None:
        self.db.delete(db_user)
        self.db.commit()

    def increment_token_version(self, db_user: User) -> User:
        """
        Atomically increment the token_version counter.
        This invalidates all JWTs previously issued to this user,
        acting as an instant global logout kill-switch.
        """
        db_user.token_version += 1
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
