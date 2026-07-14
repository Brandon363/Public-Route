from sqlalchemy import Column, Integer, String, Boolean
from Config.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    Authentication and authorisation record.

    Stores only the credentials and role needed for platform access.
    No operational profile data lives here — profile details belong
    on the entity that owns the relationship (e.g. ResourceTeam, OrganisationUnit).
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    full_name       = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role            = Column(String, nullable=False)

    # Integer counter used for stateless token revocation.
    # Incrementing this value immediately invalidates all previously issued
    # tokens for this user without requiring a blacklist table.
    token_version   = Column(Integer, default=1, nullable=False)

    is_active       = Column(Boolean, default=True, nullable=False)
