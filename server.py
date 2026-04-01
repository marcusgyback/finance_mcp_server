"""
server.py — Financial Analysis MCP Server entry point.

Starts a FastMCP server using StreamableHTTP transport.  All tools are
registered from the tools/ package.  Environment is loaded from .env before
any tool modules are imported so that storage credentials are available.

Client authentication:
  Every request must include a valid API key as a query parameter:
    http://your-server:8000/mcp?api_key=CLIENT_KEY

  Keys and their active status are managed in clients.json.
  Set "active": false to immediately revoke a client's access.
"""

import os

from dotenv import load_dotenv

# Load .env before importing tool modules that read env vars at call time.
load_dotenv()

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from auth.clients import get_client_folder, get_client_name, validate_api_key
from auth.context import client_folder
from tools.storage import register_tools as register_storage_tools

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------
mcp = FastMCP("Financial Analysis Server")

# ---------------------------------------------------------------------------
# Register all tools
# ---------------------------------------------------------------------------
register_storage_tools(mcp)

# ---------------------------------------------------------------------------
# Auth middleware — validates api_key query param on every request
# ---------------------------------------------------------------------------

_REJECTION_MESSAGES = {
    "missing": "API key required. Add ?api_key=YOUR_KEY to the MCP server URL.",
    "unknown": "API key not recognised. Contact your administrator.",
    "inactive": "Your access has been deactivated. Contact your administrator.",
}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow health-check endpoint without auth
        if request.url.path == "/health":
            return await call_next(request)

        api_key = request.query_params.get("api_key")
        valid, reason = validate_api_key(api_key)

        if not valid:
            return JSONResponse(
                status_code=401,
                content={"error": _REJECTION_MESSAGES[reason]},
            )

        # Attach client info to request state for logging
        request.state.client_name = get_client_name(api_key)

        # Set the client's folder in the context var so storage tools can
        # scope all paths without needing access to the request object.
        token = client_folder.set(get_client_folder(api_key))
        try:
            return await call_next(request)
        finally:
            client_folder.reset(token)


# ---------------------------------------------------------------------------
# ASGI app — wrap with auth middleware
# ---------------------------------------------------------------------------
_base_app = mcp.get_asgi_app()

from starlette.applications import Starlette
from starlette.routing import Route, Mount


async def health(request: Request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/", app=_base_app),
    ]
)
app.add_middleware(ApiKeyMiddleware)

# ---------------------------------------------------------------------------
# Entry point — run directly with: python server.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    uvicorn.run("server:app", host=host, port=port, reload=False)
