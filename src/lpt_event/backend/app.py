from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .config import conf
from .router import api
from .utils import add_not_found_handler
from .runtime import rt
from .logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown logic.

    Runs once when the application starts, before accepting any requests.
    This is the right place to validate connections and initialize resources.
    """
    logger.info(f"Starting app with configuration:\n{conf.model_dump_json(indent=2)}")

    # Validate database connectivity before accepting requests
    # This fails fast if database is misconfigured
    rt.validate_db()

    # Create tables and seed demo data if needed
    # Safe to call multiple times - won't recreate existing tables
    rt.initialize_models()

    yield  # Application runs here
    # Cleanup code would go after yield (none needed currently)


app = FastAPI(title=f"{conf.app_name}", lifespan=lifespan)
ui = StaticFiles(directory=conf.static_assets_path, html=True)

# CRITICAL: Order matters! API routes must be included BEFORE mounting static files
#
# FastAPI/Starlette processes routes in order:
# 1. First, check if path matches API routes (e.g., /api/events)
# 2. Then, check if path matches static file mount (e.g., /, /index.html)
#
# If we reversed the order, mounting "/" first would catch all requests
# and API routes would never be reached!
app.include_router(api)  # Must come first
app.mount("/", ui)  # Catch-all mount must come last

# Add custom 404 handler for unmatched routes
# This ensures consistent error responses
add_not_found_handler(app)
