from importlib import resources
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import Field, BaseModel
from dotenv import load_dotenv
from .._metadata import app_name, app_slug
from pydantic.fields import _Unset

# Calculate project root dynamically by walking up from this file
# Structure: /project_root/src/lpt_event/backend/config.py
# So we need to go up 4 levels to reach project root
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"

# Load environment variables from .env file if it exists
# This is useful for local development to avoid setting env vars manually
if env_file.exists():
    load_dotenv(dotenv_path=env_file)


class DatabaseConfig(BaseModel):
    port: int = Field(description="The port of the database", default=5432)
    database_name: str = Field(
        description="The name of the database", default="databricks_postgres"
    )
    instance_name: str = Field(description="The name of the database instance")


class AppConfig(BaseSettings):
    """
    Main application configuration loaded from environment variables.

    Environment variables should be prefixed with LPT_EVENT_ (based on app_slug).
    Nested configuration uses double underscore delimiter.

    Examples:
        LPT_EVENT_API_PREFIX=/api
        LPT_EVENT_DB__INSTANCE_NAME=LPT-LKB-2
        LPT_EVENT_DB__PORT=5432
        LPT_EVENT_DB__DATABASE_NAME=databricks_postgres
    """
    model_config = SettingsConfigDict(
        env_file=env_file,  # Load from .env file if present
        env_prefix=f"{app_slug.upper()}_",  # All env vars must start with LPT_EVENT_
        extra="ignore",  # Ignore extra env vars that don't match our schema
        env_nested_delimiter="__",  # Use __ to set nested config (e.g., DB__PORT sets db.port)
    )
    app_name: str = Field(default=app_name)
    api_prefix: str = Field(default="/api")  # All API routes will be mounted under this prefix
    db: DatabaseConfig = _Unset  # Database configuration (required in production)

    @property
    def static_assets_path(self) -> Path:
        """
        Returns the path to built frontend assets.

        The frontend build process outputs files to src/lpt_event/__dist__/
        which gets included in the Python package distribution.
        """
        return Path(str(resources.files(app_slug))).joinpath("__dist__")


conf = AppConfig()
