from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from Config.database import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


# ---------------------------------------------------------------------------
# Password hashing.
# Uses the bcrypt library directly. passlib 1.7.4 is incompatible with
# bcrypt >= 4.0.0 due to the removal of bcrypt.__about__, so we call
# the bcrypt API directly to avoid that runtime error.
# ---------------------------------------------------------------------------

def get_password_hash(password: str) -> str:
    """Return the bcrypt hash of the given plain-text password."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain-text password matches the stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ---------------------------------------------------------------------------
# JWT creation.
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a signed JWT access token.

    The payload will always contain:
      - sub: the user's email address
      - role: the user's role string
      - token_version: the integer counter used for emergency revocation
      - exp: the expiry timestamp

    The caller is responsible for providing 'sub', 'role', and 'token_version'
    inside the data dict.
    """
    to_encode = data.copy()

    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
