"""
auth/context.py — Request-scoped context variables.

FastMCP tool functions are plain callables with no access to the HTTP request.
We use a contextvars.ContextVar to pass per-request state (client folder prefix)
from the Starlette middleware into the tool layer without threading issues.
"""

from contextvars import ContextVar
from typing import Optional

# Set by ApiKeyMiddleware on every authenticated request.
# Tools read this to scope all storage paths to the client's folder.
client_folder: ContextVar[Optional[str]] = ContextVar("client_folder", default=None)
