from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .config import conf
from .logger import logger


def add_not_found_handler(app: FastAPI):
    """Register a custom 404 handler that supports SPA client-side routing.

    This handler enables proper client-side routing for single-page applications (SPAs)
    while maintaining correct 404 behavior for API endpoints and static assets.

    The handler implements the following logic for 404 errors:
    - API requests (paths starting with /api): Return JSON 404 error
    - Static assets (paths ending with file extensions): Return JSON 404 error
    - SPA navigation (GET requests accepting HTML): Serve index.html to allow client-side routing
    - Other 404s: Return JSON 404 error

    Args:
        app (FastAPI): The FastAPI application instance to register the handler on.

    Example:
        >>> app = FastAPI()
        >>> add_not_found_handler(app)
        >>> # Now requests to /about will serve index.html (SPA handles routing)
        >>> # But requests to /api/nonexistent will return JSON 404
        >>> # And requests to /missing.js will return JSON 404

    Note:
        This must be called after mounting static files but can be called anytime
        after the FastAPI app is created.
    """
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions, especially 404s for SPA routing support.

        Args:
            request (Request): The incoming request that caused the exception.
            exc (StarletteHTTPException): The HTTP exception that was raised.

        Returns:
            FileResponse | JSONResponse: Either the SPA index.html for client-side routing
                or a JSON error response for actual 404 errors.
        """
        logger.info(
            f"HTTP exception handler called for request {request.url.path} with status code {exc.status_code}"
        )
        if exc.status_code == 404:
            path = request.url.path
            accept = request.headers.get("accept", "")

            is_api = path.startswith(conf.api_prefix)
            is_get_page_nav = request.method == "GET" and "text/html" in accept

            # Heuristic: if the last path segment looks like a file (has a dot), don't SPA-fallback
            # This prevents serving index.html for requests like /missing.js or /logo.png
            looks_like_asset = "." in path.split("/")[-1]

            if (not is_api) and is_get_page_nav and (not looks_like_asset):
                # Let the SPA router handle it by serving the index.html
                # The frontend router (TanStack Router) will then handle the actual routing
                return FileResponse(conf.static_assets_path / "index.html")
        # Default: return the original HTTP error (JSON 404 for API, etc.)
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    app.exception_handler(StarletteHTTPException)(http_exception_handler)
