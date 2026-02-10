from typing import Annotated

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config.settings import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

# JWKS client instance (lazy loaded)
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    """Get or create JWKS client."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.jwks_url)
    return _jwks_client


class AuthenticatedUser:
    """Represents an authenticated user extracted from JWT.

    Note: user_id is a string (not UUID) because Better Auth generates
    non-UUID string IDs like '7OMgLqJ4nHFamYC3ojPQLGv0yBoUmBrS'.
    """

    def __init__(self, user_id: str, email: str | None = None):
        self.user_id = user_id
        self.email = email


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    """Extract JWT token from Bearer header or cookie."""
    if credentials and credentials.credentials:
        return credentials.credentials

    token = request.cookies.get("better-auth.jwt")
    if token:
        return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _verify_token(token: str) -> dict:
    """Verify JWT using JWKS (asymmetric) or shared secret (symmetric)."""
    # Try asymmetric verification with JWKS first
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA", "ES256", "RS256"],
            options={"verify_exp": True},
        )
        return payload
    except Exception as jwks_error:
        pass  # Fall through to symmetric

    # Fallback: Try symmetric HS256 with shared secret
    try:
        payload = jwt.decode(
            token,
            settings.better_auth_secret,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthenticatedUser:
    """FastAPI dependency that extracts and verifies the current user from JWT.

    Per spec FR-014: Extract user identity from validated JWT token.
    Per spec FR-016: user_id is NEVER accepted from client input.

    Returns:
        AuthenticatedUser with user_id from JWT 'sub' claim.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
    """
    token = _extract_token(request, credentials)
    payload = _verify_token(token)

    # Debug: log the payload
    import logging
    logging.info(f"JWT payload: {payload}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing user ID in token. Payload: {payload}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(
        user_id=user_id,
        email=payload.get("email"),
    )


async def get_current_user_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    """FastAPI dependency that returns just the current user's ID string."""
    user = await get_current_user(request, credentials)
    return user.user_id


# Type alias for dependency injection
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
