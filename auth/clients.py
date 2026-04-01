"""
auth/clients.py — Client registry and API key validation.

Reads clients.json on every check so changes take effect immediately
without requiring a server restart. To revoke a client, set their
"active" field to false in clients.json.
"""

import json
import os
from pathlib import Path
from typing import Optional

# Path to the clients file — override via CLIENTS_FILE env var.
_DEFAULT_CLIENTS_FILE = Path(__file__).parent.parent / "clients.json"


def _load_clients() -> dict:
    clients_file = Path(os.getenv("CLIENTS_FILE", str(_DEFAULT_CLIENTS_FILE)))
    if not clients_file.exists():
        return {}
    with clients_file.open() as f:
        return json.load(f)


def validate_api_key(api_key: Optional[str]) -> tuple[bool, str]:
    """
    Validate an API key against the client registry.

    Returns (is_valid, reason).
      - (True,  "ok")                     — key is known and active
      - (False, "missing")                — no key provided
      - (False, "unknown")                — key not in clients.json
      - (False, "inactive")               — key exists but active=false
    """
    if not api_key:
        return False, "missing"

    clients = _load_clients()

    if api_key not in clients:
        return False, "unknown"

    if not clients[api_key].get("active", False):
        return False, "inactive"

    return True, "ok"


def get_client_name(api_key: str) -> Optional[str]:
    """Return the client's display name, or None if not found."""
    clients = _load_clients()
    entry = clients.get(api_key)
    return entry.get("name") if entry else None


def get_client_folder(api_key: str) -> Optional[str]:
    """Return the client's storage folder prefix, or None if not found."""
    clients = _load_clients()
    entry = clients.get(api_key)
    return entry.get("folder") if entry else None
