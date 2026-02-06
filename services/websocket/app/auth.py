"""JWT Authentication for WebSocket connections.

Per T037: Validates JWT tokens passed as query parameter on WebSocket connect.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger("websocket-service")

# JWT configuration from environment
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "")

# For development without auth
ALLOW_UNAUTHENTICATED = os.environ.get("ALLOW_UNAUTHENTICATED", "false").lower() == "true"
DEFAULT_USER_ID = os.environ.get("DEFAULT_USER_ID", "")


@dataclass
class AuthResult:
    """Result of authentication attempt."""

    success: bool
    user_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class WebSocketAuthenticator:
    """Authenticates WebSocket connections via JWT token.

    The token is passed as a query parameter: ws://host/ws?token=JWT_TOKEN

    Token payload must contain:
    - sub: User ID (Better Auth format)
    - exp: Expiration timestamp
    """

    def __init__(
        self,
        secret: str = JWT_SECRET,
        algorithm: str = JWT_ALGORITHM,
        issuer: str | None = JWT_ISSUER or None,
    ):
        self.secret = secret
        self.algorithm = algorithm
        self.issuer = issuer

    def authenticate(self, token: str | None) -> AuthResult:
        """Authenticate a JWT token and extract user ID.

        Args:
            token: JWT token string (from query parameter)

        Returns:
            AuthResult with success status and user_id or error details
        """
        # Development mode - allow unauthenticated connections
        if ALLOW_UNAUTHENTICATED and not token:
            if DEFAULT_USER_ID:
                logger.warning(
                    "auth_bypass",
                    extra={"user_id": DEFAULT_USER_ID},
                )
                return AuthResult(success=True, user_id=DEFAULT_USER_ID)
            return AuthResult(
                success=False,
                error_code="AUTH_FAILED",
                error_message="No token provided and no default user configured",
            )

        if not token:
            return AuthResult(
                success=False,
                error_code="AUTH_FAILED",
                error_message="No authentication token provided",
            )

        if not self.secret:
            logger.error("JWT_SECRET not configured")
            return AuthResult(
                success=False,
                error_code="INTERNAL_ERROR",
                error_message="Authentication service misconfigured",
            )

        try:
            # Decode and verify the token
            options = {"require": ["sub", "exp"]}
            if self.issuer:
                options["require"].append("iss")

            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options=options,
                issuer=self.issuer if self.issuer else None,
            )

            user_id = payload.get("sub")
            if not user_id:
                return AuthResult(
                    success=False,
                    error_code="AUTH_FAILED",
                    error_message="Token missing user identifier",
                )

            logger.info(
                "auth_success",
                extra={"user_id": user_id},
            )

            return AuthResult(success=True, user_id=user_id)

        except ExpiredSignatureError:
            logger.warning("auth_token_expired")
            return AuthResult(
                success=False,
                error_code="TOKEN_EXPIRED",
                error_message="Authentication token has expired",
            )

        except InvalidTokenError as e:
            logger.warning(
                "auth_token_invalid",
                extra={"error": str(e)},
            )
            return AuthResult(
                success=False,
                error_code="AUTH_FAILED",
                error_message="Invalid authentication token",
            )

        except Exception as e:
            logger.error(
                "auth_error",
                extra={"error": str(e)},
            )
            return AuthResult(
                success=False,
                error_code="INTERNAL_ERROR",
                error_message="Authentication failed due to internal error",
            )


# Global authenticator instance
authenticator = WebSocketAuthenticator()


def authenticate_token(token: str | None) -> AuthResult:
    """Convenience function to authenticate a token."""
    return authenticator.authenticate(token)
