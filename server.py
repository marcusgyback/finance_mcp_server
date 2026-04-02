"""
server.py — Financial Analysis MCP Server entry point.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from auth.clients import get_client_folder, get_client_name, validate_api_key
from auth.context import client_folder
from tools.storage import register_tools as register_storage_tools

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Financial Analysis Server",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)
register_storage_tools(mcp)

# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------
_REJECTION_MESSAGES = {
    "missing": "API key required. Add ?api_key=YOUR_KEY to the MCP server URL.",
    "unknown": "API key not recognised. Contact your administrator.",
    "inactive": "Your access has been deactivated. Contact your administrator.",
}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        api_key = request.query_params.get("api_key")
        valid, reason = validate_api_key(api_key)

        if not valid:
            return JSONResponse(
                status_code=401,
                content={"error": _REJECTION_MESSAGES[reason]},
            )

        request.state.client_name = get_client_name(api_key)
        token = client_folder.set(get_client_folder(api_key))
        try:
            return await call_next(request)
        finally:
            client_folder.reset(token)


# ---------------------------------------------------------------------------
# ASGI app with MCP lifespan
# ---------------------------------------------------------------------------
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app):
    async with mcp_app.router.lifespan_context(app):
        yield


async def health(request: Request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/health", health),
        Mount("/", app=mcp_app),
    ],
)
app.add_middleware(ApiKeyMiddleware)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=False)
