"""
Secret token authentication dependency.
"""
from fastapi import Header, HTTPException, status
from app.config import settings

async def verify_secret_token(authorization: str = Header(None)) -> None:
    """
    Verify that the Authorization header matches the configured secret token.
    If no secret_token is set, allow all requests.
    """
    secret = settings.secret_token
    if not secret:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    token = authorization.split(" ", 1)[1]
    if token != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )