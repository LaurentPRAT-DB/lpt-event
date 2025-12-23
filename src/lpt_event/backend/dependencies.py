from databricks.sdk import WorkspaceClient
from fastapi import Header
from typing import Annotated, Generator
from sqlmodel import Session
from sqlalchemy import create_engine, event
from .runtime import rt
from .config import conf
from .logger import logger


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

    # Create an on-behalf-of WorkspaceClient for this request
    logger.debug("Creating OBO database session")
    obo_ws = WorkspaceClient(token=token, auth_type="pat")

    # Get the database instance details
    instance = obo_ws.database.get_database_instance(conf.db.instance_name)

    # Build the engine URL with the OBO user's identity
    prefix = "postgresql+psycopg"
    host = instance.read_write_dns
    port = conf.db.port
    database = conf.db.database_name

    # Get the username for this OBO user
    username = obo_ws.current_user.me().user_name
    engine_url = f"{prefix}://{username}:@{host}:{port}/{database}"

    # Create a short-lived engine for this request
    engine = create_engine(
        engine_url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args={"sslmode": "require"},
    )

    # Generate database credentials for this OBO user
    def _before_connect(dialect, conn_rec, cargs, cparams):
        cred = obo_ws.database.generate_database_credential(
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
