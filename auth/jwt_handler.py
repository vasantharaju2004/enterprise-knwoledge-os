import os
import jwt
import datetime
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
EXPIRY_HOURS = 24


def create_token(user_id: str, org_id: str) -> str:
    """
    creates a signed token containing the user's identity and
    organisation. Anything encoded here is what get_current_user
    will trust on every subsequent authenticated request - this
    is the mechanism that replaces every hardcoded "dev_user"
    default across the codebase with a real, verified value.
    """
    payload = {
        "user_id": user_id,
        "org_id": org_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=EXPIRY_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Decodes and verifies a token's signature and expiry. Raises
    jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure -
    callers must handle these explicitly rather than assuming a
    token is always valid.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
