#!/usr/bin/env python3
"""
manage_clients.py — CLI tool for managing MCP server clients.

Usage:
    python manage_clients.py list
    python manage_clients.py add    --name "Acme Corp" --folder "acme-corp" [--note "Trial until 2026-07-01"]
    python manage_clients.py revoke --key KEY
    python manage_clients.py activate --key KEY
    python manage_clients.py delete --key KEY
    python manage_clients.py show   --key KEY
"""

import argparse
import json
import os
import secrets
import sys
from pathlib import Path

CLIENTS_FILE = Path(os.getenv("CLIENTS_FILE", "clients.json"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load() -> dict:
    if not CLIENTS_FILE.exists():
        return {}
    with CLIENTS_FILE.open() as f:
        return json.load(f)


def _save(clients: dict) -> None:
    with CLIENTS_FILE.open("w") as f:
        json.dump(clients, f, indent=2)
        f.write("\n")


def _generate_key() -> str:
    """Generate a cryptographically secure 32-byte hex API key."""
    return secrets.token_hex(32)


def _status(active: bool) -> str:
    return "active" if active else "INACTIVE"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list(args) -> None:
    clients = _load()
    if not clients:
        print("No clients registered.")
        return

    col_key  = max(len(k) for k in clients) + 2
    col_name = max(len(v["name"]) for v in clients.values()) + 2
    col_folder = max(len(v.get("folder", "")) for v in clients.values()) + 2

    header = (
        f"{'API Key':<{col_key}}"
        f"{'Name':<{col_name}}"
        f"{'Folder':<{col_folder}}"
        f"{'Status':<10}"
        f"Note"
    )
    print(header)
    print("-" * len(header))

    for key, data in clients.items():
        print(
            f"{key:<{col_key}}"
            f"{data['name']:<{col_name}}"
            f"{data.get('folder', ''):<{col_folder}}"
            f"{_status(data.get('active', False)):<10}"
            f"{data.get('note', '')}"
        )

    total   = len(clients)
    active  = sum(1 for v in clients.values() if v.get("active"))
    print(f"\n{total} client(s) — {active} active, {total - active} inactive.")


def cmd_add(args) -> None:
    clients = _load()

    # Derive folder from name if not provided
    folder = args.folder or args.name.lower().replace(" ", "-")

    # Check folder is not already in use
    for key, data in clients.items():
        if data.get("folder") == folder:
            print(f"Error: folder '{folder}' is already assigned to '{data['name']}' ({key[:16]}...).")
            sys.exit(1)

    key = _generate_key()
    clients[key] = {
        "name":   args.name,
        "folder": folder,
        "active": True,
        "note":   args.note or "",
    }
    _save(clients)

    mcp_url = f"https://your-server.com/mcp?api_key={key}"

    print(f"\nClient added successfully.")
    print(f"\n  Name   : {args.name}")
    print(f"  Folder : {folder}")
    print(f"  Key    : {key}")
    print(f"\n  MCP URL to send to client:")
    print(f"  {mcp_url}")
    print(f"\nRemember to create the folder '{folder}/' in Filestash.")


def cmd_revoke(args) -> None:
    clients = _load()
    if args.key not in clients:
        print(f"Error: key not found.")
        sys.exit(1)
    if not clients[args.key].get("active"):
        print(f"Client '{clients[args.key]['name']}' is already inactive.")
        return
    clients[args.key]["active"] = False
    _save(clients)
    print(f"Access revoked for '{clients[args.key]['name']}'. Effective immediately.")


def cmd_activate(args) -> None:
    clients = _load()
    if args.key not in clients:
        print(f"Error: key not found.")
        sys.exit(1)
    if clients[args.key].get("active"):
        print(f"Client '{clients[args.key]['name']}' is already active.")
        return
    clients[args.key]["active"] = True
    _save(clients)
    print(f"Access restored for '{clients[args.key]['name']}'. Effective immediately.")


def cmd_delete(args) -> None:
    clients = _load()
    if args.key not in clients:
        print(f"Error: key not found.")
        sys.exit(1)
    name = clients[args.key]["name"]
    confirm = input(f"Permanently delete '{name}'? This cannot be undone. Type YES to confirm: ")
    if confirm != "YES":
        print("Aborted.")
        return
    del clients[args.key]
    _save(clients)
    print(f"Client '{name}' deleted.")


def cmd_show(args) -> None:
    clients = _load()
    if args.key not in clients:
        print(f"Error: key not found.")
        sys.exit(1)
    data = clients[args.key]
    print(f"\n  Name   : {data['name']}")
    print(f"  Folder : {data.get('folder', '(none)')}")
    print(f"  Status : {_status(data.get('active', False))}")
    print(f"  Note   : {data.get('note', '')}")
    print(f"  Key    : {args.key}")
    print(f"\n  MCP URL:")
    print(f"  https://your-server.com/mcp?api_key={args.key}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage MCP server clients.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="List all clients")

    # add
    p_add = sub.add_parser("add", help="Add a new client and generate their API key")
    p_add.add_argument("--name",   required=True, help='Client display name, e.g. "Acme Corp"')
    p_add.add_argument("--folder", required=False, help="Filestash folder name (derived from name if omitted)")
    p_add.add_argument("--note",   required=False, help='Internal note, e.g. "Trial until 2026-07-01"')

    # revoke
    p_revoke = sub.add_parser("revoke", help="Revoke a client's access (sets active=false)")
    p_revoke.add_argument("--key", required=True, help="The client's API key")

    # activate
    p_activate = sub.add_parser("activate", help="Restore a previously revoked client's access")
    p_activate.add_argument("--key", required=True, help="The client's API key")

    # delete
    p_delete = sub.add_parser("delete", help="Permanently remove a client from the registry")
    p_delete.add_argument("--key", required=True, help="The client's API key")

    # show
    p_show = sub.add_parser("show", help="Show full details for a client including their MCP URL")
    p_show.add_argument("--key", required=True, help="The client's API key")

    args = parser.parse_args()

    commands = {
        "list":     cmd_list,
        "add":      cmd_add,
        "revoke":   cmd_revoke,
        "activate": cmd_activate,
        "delete":   cmd_delete,
        "show":     cmd_show,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
