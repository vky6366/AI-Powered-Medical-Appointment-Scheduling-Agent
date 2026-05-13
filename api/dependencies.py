from __future__ import annotations

# api/dependencies.py
# Reusable FastAPI dependency for authenticated routes.

from fastapi import Header, HTTPException, status

from agents.auth import verify_access_token


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict:
    """
    FastAPI dependency that validates the Bearer JWT and returns the
    decoded payload (e.g. {"user_id": 42}).

    Usage::

        @router.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    try:
        token = authorization.replace("Bearer ", "")
        payload = verify_access_token(token)
        return payload

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
