"""
Runtime utilities for database access.

We keep the Databricks-backed Postgres configuration for production, but also
support a simple in-memory SQLite database for local development and mocking.
"""

from functools import cached_property

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, text

from .config import AppConfig, conf
from .logger import logger


class Runtime:
    def __init__(self):
        self.config: AppConfig = conf

    @cached_property
    def ws(self) -> WorkspaceClient:
        # note - this workspace client is usually an SP-based client
        # in development it usually uses the DATABRICKS_CONFIG_PROFILE
        return WorkspaceClient()

    @cached_property
    def engine_url(self) -> str:
        """
        Build the SQLAlchemy engine URL.

        For local/mock development, you can set the DB instance name to
        ``sqlite-memory`` to use an in-memory SQLite DB instead.
        """
        if (
            isinstance(self.config.db.instance_name, str)
            and self.config.db.instance_name.lower() == "sqlite-memory"
        ):
            # Shared in-memory SQLite for local play and mocking
            # Using file::memory:?cache=shared ensures all connections see the same database
            # The 'uri=true' parameter is required when using the file: URI syntax
            return "sqlite:///file::memory:?cache=shared&uri=true"

        # For production: Get Databricks Postgres instance details
        instance = self.ws.database.get_database_instance(self.config.db.instance_name)

        # Use psycopg (version 3) driver for better performance and async support
        prefix = "postgresql+psycopg"
        host = instance.read_write_dns
        port = self.config.db.port
        database = self.config.db.database_name

        # Username is either the service principal client_id or the current user's email
        # Password is omitted here and will be injected via _before_connect callback
        # This allows for dynamic credential generation per connection attempt
        username = (
            self.ws.config.client_id
            if self.ws.config.client_id
            else self.ws.current_user.me().user_name
        )
        return f"{prefix}://{username}:@{host}:{port}/{database}"

    def _before_connect(self, dialect, conn_rec, cargs, cparams):
        """
        SQLAlchemy connection event callback to inject fresh database credentials.

        This callback runs before each database connection is established.
        For Databricks Postgres, we generate short-lived credentials dynamically
        rather than using a static password. This improves security by:
        1. Ensuring credentials are always fresh (not expired)
        2. Enabling credential rotation without app restart
        3. Supporting different credential scopes per connection if needed
        """
        if self.engine_url.startswith("sqlite"):
            # SQLite doesn't need authentication
            return

        # Generate a fresh token-based credential for Databricks Postgres
        # This token typically has a TTL of 1 hour
        cred = self.ws.database.generate_database_credential(
            instance_names=[self.config.db.instance_name]
        )
        cparams["password"] = cred.token

    @cached_property
    def engine(self) -> Engine:
        if self.engine_url.startswith("sqlite"):
            # SQLite configuration for local development
            engine = create_engine(
                self.engine_url,
                connect_args={
                    "check_same_thread": False,  # Allow SQLite to be used across threads (FastAPI uses thread pool)
                    "uri": True  # Enable URI syntax for file::memory: path
                },
                poolclass=StaticPool,  # Use StaticPool to maintain a single in-memory connection
            )
        else:
            # Databricks Postgres configuration for production
            engine = create_engine(
                self.engine_url,
                pool_recycle=45 * 60,  # Recycle connections after 45 minutes to avoid stale credentials
                connect_args={"sslmode": "require"},  # Enforce SSL for security
                pool_size=4,  # Limit connection pool size to avoid overwhelming the database
            )
            # Register callback to inject fresh credentials before each connection
            event.listens_for(engine, "do_connect")(self._before_connect)
        return engine

    def get_session(self) -> Session:
        return Session(self.engine)

    def validate_db(self) -> None:
        """Validate DB connectivity, skipping heavy checks for local SQLite."""
        if self.engine_url.startswith("sqlite"):
            logger.info("Using in-memory SQLite database for local development")
            return

        logger.info(
            f"Validating database connection to instance {self.config.db.instance_name}"
        )
        # check if the database instance exists
        try:
            self.ws.database.get_database_instance(self.config.db.instance_name)
        except NotFound:
            raise ValueError(
                f"Database instance {self.config.db.instance_name} does not exist"
            )

        # check if a connection to the database can be established
        try:
            with self.get_session() as session:
                session.connection().execute(text("SELECT 1"))
                session.close()

        except Exception:
            raise ConnectionError("Failed to connect to the database")

        logger.info(
            f"Database connection to instance {self.config.db.instance_name} validated successfully"
        )

    def initialize_models(self) -> None:
        """Create tables and seed some mock data for development."""
        from .models import Event  # local import to avoid circularity

        logger.info("Initializing database models")
        # Create all tables defined via SQLModel metadata
        # This is idempotent - it won't fail if tables already exist
        SQLModel.metadata.create_all(self.engine)

        # Seed demo data only on first run to avoid duplicates
        # This is helpful for quick local testing and demos
        with self.get_session() as session:
            # Use SQLModel query instead of raw SQL to check if table is empty
            from sqlmodel import select
            existing_events = session.exec(select(Event)).first()
            if existing_events is None:
                # Table is empty - seed with demo data
                logger.info("Seeding mock events data")
                from datetime import datetime

                now_year = datetime.utcnow().year
                demo_events = [
                    Event(
                        title="Data & AI Meetup",
                        short_description="Monthly community meetup on data and AI.",
                        detailed_description=(
                            "Join fellow data engineers and scientists for lightning talks, "
                            "live demos, and networking. Snacks and drinks provided."
                        ),
                        city="San Francisco",
                        days_of_week=["Thursday"],
                        cost_usd=0.0,
                        picture_url="https://images.pexels.com/photos/1181567/pexels-photo-1181567.jpeg",
                    ),
                    Event(
                        title="Weekend Hackathon",
                        short_description="48-hour product hackathon.",
                        detailed_description=(
                            "Form a team, ship a prototype, and pitch to a panel of judges. "
                            "Tracks include AI, analytics, and developer tooling."
                        ),
                        city="New York",
                        days_of_week=["Saturday", "Sunday"],
                        cost_usd=49.0,
                        picture_url="https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg",
                    ),
                    Event(
                        title="Analytics Workshop",
                        short_description="Hands-on workshop on modern analytics stacks.",
                        detailed_description=(
                            "A full-day workshop covering ingestion, transformation, "
                            "and visualization best practices using modern tooling."
                        ),
                        city="London",
                        days_of_week=["Wednesday"],
                        cost_usd=199.0,
                        picture_url="https://images.pexels.com/photos/1181673/pexels-photo-1181673.jpeg",
                    ),
                ]
                for ev in demo_events:
                    session.add(ev)
                session.commit()

        logger.info("Database models initialized successfully")


rt = Runtime()
