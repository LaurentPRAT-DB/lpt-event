from databricks.sdk import WorkspaceClient
from fastapi import Header, Request
from typing import Annotated, Generator
from sqlmodel import Session
from sqlalchemy import create_engine, event
import base64
import json
from .runtime import rt
from .config import conf
from .logger import logger


def _extract_username_from_token(token: str) -> str:
    """
    Extract username from JWT token without verification.

    Databricks OBO tokens are JWTs that contain user information in the payload.
    We don't verify the signature since the token came from Databricks infrastructure
    via the X-Forwarded-Access-Token header, which is only set by Databricks Apps.
    This is safe because the token never passes through untrusted networks.
    """
    try:
        # JWT tokens have format: header.payload.signature
        # We only need the payload (middle section) for user information
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # Decode the payload (second part) from base64
        # JWT uses URL-safe base64 encoding without padding
        payload = parts[1]

        # Add padding if needed - base64 strings must be multiples of 4
        # The modulo operation determines how many padding chars ('=') to add
        padding = 4 - len(payload) % 4
        if padding != 4:  # Only add padding if actually needed
            payload += '=' * padding

        # Decode from base64 and parse JSON to get claims
        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)

        # Try common username claims in order of preference
        # Different OAuth providers use different claim names for username
        for claim in ['email', 'sub', 'upn', 'preferred_username']:
            if claim in claims:
                username = claims[claim]
                logger.debug(f"Extracted username from token claim '{claim}': {username}")
                return username

        raise ValueError(f"No username claim found in token. Available claims: {list(claims.keys())}")

    except Exception as e:
        logger.error(f"Failed to extract username from OBO token: {e}")
        raise ValueError(f"Could not extract username from OBO token: {e}")


def get_obo_ws(
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
) -> WorkspaceClient:
    """
    Returns a Databricks Workspace client with authentication behalf of user.
    If the request contains an X-Forwarded-Access-Token header, on behalf of user authentication is used.

    Example usage:
    @api.get("/items/")
    async def read_items(obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)]):
        # do something with the obo_ws
        ...
    """

    if not token:
        raise ValueError(
            "OBO token is not provided in the header X-Forwarded-Access-Token"
        )

    # Create a workspace client using the OBO token
    # auth_type="pat" tells the SDK to use the token as a personal access token
    # We explicitly set this to avoid conflicts with default service principal authentication
    return WorkspaceClient(
        token=token, auth_type="pat"
    )


def get_session() -> Generator[Session, None, None]:
    """
    Returns a SQLModel session.
    """
    with rt.get_session() as session:
        yield session


def get_obo_session(
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
) -> Generator[Session, None, None]:
    """
    Returns a SQLModel session for the authenticated user.

    Note: Due to OBO token limitations, database connections use the service principal.
    The user's identity (extracted from the OBO token) is available for application-level
    audit trails, but the actual database connection is made as the service principal.

    For true per-user database connections, the OAuth app would need additional scopes
    to generate database credentials on behalf of users.

    For local development (no OBO token), falls back to the default session.

    Example usage:
    @api.get("/items/")
    async def read_items(session: Annotated[Session, Depends(get_obo_session)]):
        # session uses service principal for database access
        # user identity can be tracked at application level
        ...
    """

    # Always use the default session (service principal database connection)
    # This is because:
    # 1. The OBO token scope doesn't include database credential generation
    # 2. Service principal has been granted explicit permission to connect to the database
    # 3. Database-level user authentication would require OAuth app scope changes
    if token:
        # Extract username for application-level logging and audit trails
        # This allows us to track which user made each API request
        username = _extract_username_from_token(token)
        logger.debug(f"Request from user: {username} (using service principal for database access)")
    else:
        # No OBO token present - running in local development mode
        logger.debug("Using default session (local development)")

    with rt.get_session() as session:
        yield session
