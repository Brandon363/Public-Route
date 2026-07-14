import os
from dotenv import load_dotenv
import urllib.parse
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Separate secret used to deterministically tokenise citizen PII (e.g. phone
# numbers) so it can be looked up again without storing the raw value.
# Deliberately NOT the JWT signing key: rotating SECRET_KEY for an auth
# incident must not also break every existing citizen_contact_token lookup,
# and a leaked JWT key must not also become a PII-tokenisation oracle.
PII_TOKEN_KEY = os.getenv("PII_TOKEN_KEY")
if not PII_TOKEN_KEY:
    logger.warning(
        "PII_TOKEN_KEY is not set — falling back to SECRET_KEY for PII "
        "tokenisation. Set a dedicated PII_TOKEN_KEY before pilot/production use."
    )
    PII_TOKEN_KEY = SECRET_KEY

LOCAL_POSTGRES_SERVER = os.getenv("LOCAL_POSTGRES_SERVER")
LOCAL_POSTGRES_DATABASE = os.getenv("LOCAL_POSTGRES_DATABASE")
LOCAL_POSTGRES_USERNAME = os.getenv("LOCAL_POSTGRES_USERNAME")
LOCAL_POSTGRES_PASSWORD = os.getenv("LOCAL_POSTGRES_PASSWORD")
LOCAL_POSTGRES_PORT = os.getenv("LOCAL_POSTGRES_PORT")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    local_postgres_server = os.getenv("LOCAL_POSTGRES_SERVER", "localhost")
    local_postgres_database = os.getenv("LOCAL_POSTGRES_DATABASE")
    local_postgres_username = os.getenv("LOCAL_POSTGRES_USERNAME")
    local_postgres_password = os.getenv("LOCAL_POSTGRES_PASSWORD")
    local_postgres_port = os.getenv("LOCAL_POSTGRES_PORT", "5432")

    local_password = urllib.parse.quote_plus(local_postgres_password) if local_postgres_password else ""

    connection_string = f"{local_postgres_username}:{local_password}@{local_postgres_server}:{local_postgres_port}/{local_postgres_database}"
    DATABASE_URL = f"postgresql+psycopg2://{connection_string}"

class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()