from fastapi import Header, HTTPException
from auth.jwt_handler import verify_token


def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Expects header : Authorization: Bearer <token>
    Returns {"user_id":...,"org_id":...} or raise 401.
    """
    if not authorization.startswith("Bearer"):
        raise HTTPException(
            status_code=401, detail="Missing or malformed Authorization header."
        )

    token = authorization.removeprefix("Bearer").strip()

    try:
        payload = verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"user_id": payload["user_id"], "org_id": payload["org_id"]}
