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
    We don't verify the signature since the token came from Databricks infrastructure.
    """
    try:
        # JWT tokens have format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # Decode the payload (second part)
        # Add padding if needed for base64 decoding
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)

        # Try common username claims in order of preference
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

    return WorkspaceClient(
        token=token, auth_type="pat"
    )  # set pat explicitly to avoid issues with SP client


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
    Returns a SQLModel session with on-behalf-of user authentication.

    When running on Databricks with an OBO token, this creates a database connection
    using credentials for the authenticated user. This ensures proper audit trails
    and row-level security enforcement.

    For local development (no OBO token), falls back to the default session.

    Example usage:
    @api.get("/items/")
    async def read_items(session: Annotated[Session, Depends(get_obo_session)]):
        # session is authenticated as the current user
        ...
    """

    # For local development or SQLite, use the default session
    if not token or rt.engine_url.startswith("sqlite"):
        logger.debug("Using default session (local development or SQLite)")
        with rt.get_session() as session:
            yield session
        return

    # Extract username from the OBO token
    # (We can't call current_user.me() because OBO tokens have limited scopes)
    username = _extract_username_from_token(token)
    logger.debug(f"Creating OBO database session for user: {username}")

    # Create an on-behalf-of WorkspaceClient for this request
    obo_ws = WorkspaceClient(token=token, auth_type="pat")

    # Use the service principal's workspace client to get database instance details
    # (user tokens don't have permission to read database instance metadata)
    instance = rt.ws.database.get_database_instance(conf.db.instance_name)

    # Build the engine URL with the OBO user's identity
    prefix = "postgresql+psycopg"
    host = instance.read_write_dns
    port = conf.db.port
    database = conf.db.database_name
    engine_url = f"{prefix}://{username}:@{host}:{port}/{database}"

    # Create a short-lived engine for this request
    engine = create_engine(
        engine_url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args={"sslmode": "require"},
    )

    # Generate database credentials using the service principal
    # (OBO tokens don't have permission to generate database credentials)
    # The username in the connection string ensures the user connects as themselves
    def _before_connect(dialect, conn_rec, cargs, cparams):
        cred = rt.ws.database.generate_database_credential(
            instance_names=[conf.db.instance_name]
        )
        cparams["password"] = cred.token

    event.listens_for(engine, "do_connect")(_before_connect)

    # Create and yield the session
    try:
        with Session(engine) as session:
            yield session
    finally:
        # Clean up the engine
        engine.dispose()
