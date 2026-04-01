# Financial Analysis MCP Server — Full Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [How It Works](#2-how-it-works)
3. [Project Structure](#3-project-structure)
4. [Setup & Installation](#4-setup--installation)
5. [Configuration Reference](#5-configuration-reference)
6. [Client Management](#6-client-management)
7. [Client Management CLI](#7-client-management-cli)
8. [Connecting from Claude](#8-connecting-from-claude)
9. [Storage Tools Reference](#9-storage-tools-reference)
10. [Workflow Tools Reference](#10-workflow-tools-reference)
11. [Deploying with Docker](#11-deploying-with-docker)
12. [Testing the Server](#12-testing-the-server)
13. [Adding Your Workflow Logic](#13-adding-your-workflow-logic)
14. [Security Model](#14-security-model)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Overview

This is a Python-based **MCP (Model Context Protocol) server** that gives Claude access to a set of tools for reading and writing files in cloud storage (Filestash), and for running proprietary financial analysis workflows.

**Key properties:**

- Clients connect using their own claude.ai subscription — you do not pay for their Claude usage
- Your server logic (workflows, business rules) is completely hidden from clients — they only see tool names and results
- Each client is isolated to their own folder in Filestash
- Access can be revoked per client at any time without restarting the server

---

## 2. How It Works

```
Client (claude.ai)
      │
      │  Uses their own Claude subscription
      │  Connects MCP server via URL + API key
      ▼
Financial Analysis MCP Server  (your server, your code)
      │
      ├── Validates API key → identifies client → scopes to their folder
      ├── Claude calls tools → server executes them → returns results
      │
      ▼
Filestash (cloud storage)
      ├── acme-corp/
      │       ├── reports/
      │       └── outputs/
      └── beta-inc/
              ├── reports/
              └── outputs/
```

1. The client adds your server URL to their Claude settings once
2. From that point, Claude automatically has access to all tools you define
3. When the client asks Claude to analyse a document, Claude calls your tools behind the scenes
4. Your server fetches the file, runs the logic, and returns the result to Claude
5. Claude presents the result to the client in natural language

The client never sees your code, your prompts, or your workflow logic.

---

## 3. Project Structure

```
financial-mcp-server/
├── server.py                  # Entry point — starts the MCP server
├── clients.json               # Client registry — add/revoke clients here
├── .env                       # Your credentials (never commit this)
├── .env.example               # Template for .env
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container deployment
│
├── auth/
│   ├── clients.py             # Client registry logic (load, validate, lookup)
│   └── context.py             # Per-request context variable (folder scoping)
│
├── storage/
│   └── client.py              # Filestash/S3 abstraction (boto3)
│
└── tools/
    ├── storage.py             # 7 cloud storage tools (fully implemented)
    └── workflows.py           # 3 financial workflow tools (shells to fill in)
```

---

## 4. Setup & Installation

### Prerequisites

- Python 3.12 or higher
- A running Filestash instance with S3-compatible API enabled
- Access credentials for your Filestash bucket

### Steps

**1. Clone / download the project**

```bash
cd financial-mcp-server
```

**2. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**3. Create your environment file**

```bash
cp .env.example .env
```

Open `.env` and fill in your values (see [Configuration Reference](#5-configuration-reference)).

**4. Add your first client** (see [Client Management](#6-client-management))

**5. Start the server**

```bash
python server.py
```

The server starts on `http://0.0.0.0:8000` by default. You should see:

```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 5. Configuration Reference

All configuration is done through environment variables in your `.env` file.

| Variable | Required | Description | Example |
|---|---|---|---|
| `S3_ENDPOINT_URL` | Yes | Your Filestash S3-compatible endpoint | `https://filestash.yourcompany.com/api/s3` |
| `S3_ACCESS_KEY` | Yes | Filestash access key ID | `myaccesskey` |
| `S3_SECRET_KEY` | Yes | Filestash secret access key | `mysecretkey` |
| `S3_BUCKET_NAME` | Yes | The bucket all client files live in | `financial-data` |
| `S3_REGION` | No | Region name (Filestash ignores this, default: `us-east-1`) | `us-east-1` |
| `MCP_HOST` | No | Host to bind to (default: `0.0.0.0`) | `0.0.0.0` |
| `MCP_PORT` | No | Port to listen on (default: `8000`) | `8000` |
| `CLIENTS_FILE` | No | Path to clients.json (default: project root) | `clients.json` |

**Example `.env`:**

```
S3_ENDPOINT_URL=https://filestash.yourcompany.com/api/s3
S3_ACCESS_KEY=myaccesskey
S3_SECRET_KEY=mysecretkey
S3_BUCKET_NAME=financial-data
S3_REGION=us-east-1
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

---

## 6. Client Management

Clients are managed in `clients.json` at the project root. The file is re-read on every request — changes take effect immediately with no server restart required.

### File format

```json
{
  "UNIQUE_API_KEY_FOR_CLIENT": {
    "name": "Client Display Name",
    "folder": "client-folder-in-filestash",
    "active": true,
    "note": "Any internal note — not shown to client"
  }
}
```

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Human-readable name, used in server logs |
| `folder` | Yes | The folder prefix in Filestash this client is scoped to |
| `active` | Yes | `true` = access granted, `false` = access revoked |
| `note` | No | Internal notes (trial dates, plan type, etc.) |

### Adding a new client

1. Generate a strong, unique API key (e.g. `openssl rand -hex 32` in a terminal)
2. Add an entry to `clients.json`:

```json
{
  "a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0": {
    "name": "Acme Corp",
    "folder": "acme-corp",
    "active": true,
    "note": "Onboarded 2026-04-01, trial until 2026-07-01"
  }
}
```

3. Create the matching folder in Filestash (`acme-corp/`)
4. Send the client their MCP server URL (see [Connecting from Claude](#7-connecting-from-claude))

### Revoking a client (killswitch)

Set `"active": false` in `clients.json`:

```json
{
  "a3f9b2c1...": {
    "name": "Acme Corp",
    "folder": "acme-corp",
    "active": false,
    "note": "Subscription ended 2026-07-01"
  }
}
```

The client's next tool call will receive:
```
Your access has been deactivated. Contact your administrator.
```

No server restart is needed. Other clients are completely unaffected.

### Example with multiple clients

```json
{
  "KEY_FOR_ACME": {
    "name": "Acme Corp",
    "folder": "acme-corp",
    "active": true,
    "note": "Enterprise plan"
  },
  "KEY_FOR_BETA": {
    "name": "Beta Inc",
    "folder": "beta-inc",
    "active": true,
    "note": "Starter plan, trial until 2026-06-01"
  },
  "KEY_FOR_GAMMA": {
    "name": "Gamma Ltd",
    "folder": "gamma-ltd",
    "active": false,
    "note": "Cancelled 2026-03-15"
  }
}
```

---

## 7. Client Management CLI

`manage_clients.py` is a command-line tool for adding, revoking, and inspecting clients without manually editing `clients.json`.

### List all clients

```bash
python manage_clients.py list
```

Output:
```
API Key                                                           Name        Folder      Status    Note
---------------------------------------------------------------------------------------------------------
a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0  Acme Corp   acme-corp   active    Trial until 2026-07-01
9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8  Beta Inc    beta-inc    INACTIVE  Subscription cancelled

2 client(s) — 1 active, 1 inactive.
```

### Add a new client

```bash
python manage_clients.py add --name "Acme Corp" --folder "acme-corp" --note "Trial until 2026-07-01"
```

Output:
```
Client added successfully.

  Name   : Acme Corp
  Folder : acme-corp
  Key    : a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0

  MCP URL to send to client:
  https://your-server.com/mcp?api_key=a3f9b2c1d4e5f6a7...

Remember to create the folder 'acme-corp/' in Filestash.
```

The `--folder` argument is optional — if omitted it is derived from the name (`"Acme Corp"` → `"acme-corp"`).

Copy the MCP URL and send it to the client. That is all they need.

### Revoke a client (killswitch)

```bash
python manage_clients.py revoke --key a3f9b2c1d4e5f6a7...
```

Takes effect immediately. The client's next tool call is rejected. No restart needed.

### Restore a revoked client

```bash
python manage_clients.py activate --key a3f9b2c1d4e5f6a7...
```

### Show a client's full details

```bash
python manage_clients.py show --key a3f9b2c1d4e5f6a7...
```

Useful when you need to look up a client's MCP URL again.

### Permanently delete a client

```bash
python manage_clients.py delete --key a3f9b2c1d4e5f6a7...
```

Prompts for confirmation before deleting. This is permanent — use `revoke` if you may want to reinstate them.

---

## 8. Connecting from Claude

Each client connects once and never needs to do it again. Give them these instructions:

---

**Instructions for your clients:**

1. Go to [claude.ai](https://claude.ai) and sign in
2. Click your profile icon → **Settings**
3. Go to the **Integrations** or **MCP Servers** section
4. Click **Add MCP Server**
5. Enter the following:
   - **Name:** Financial Analysis Tools *(or any name they prefer)*
   - **URL:** `https://your-server-domain.com/mcp?api_key=THEIR_API_KEY`
6. Click **Save**

From this point, Claude will automatically have access to all tools whenever the client starts a conversation. They can ask Claude naturally:

> *"Read the PDF at reports/Q4-2025.pdf and summarise the revenue figures"*

> *"Compare reports/budget-2025.xlsx and reports/actuals-2025.xlsx"*

> *"List all files in my reports folder"*

---

**Important:** Each client gets their own unique URL with their own `api_key`. Do not share keys between clients.

---

## 8. Storage Tools Reference

These 7 tools are fully implemented and ready to use.

All paths are relative to the client's own folder in Filestash. A client with folder `acme-corp` who passes `reports/Q4.pdf` will access `acme-corp/reports/Q4.pdf` — the scoping is automatic and invisible to them.

---

### `list_folder`

List files and folders at a given path.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | No | `""` | Folder prefix to list. Empty string lists the root. |

**Example usage in Claude:**
> *"List all files in my reports folder"*

**Example output:**
```
Contents of 'reports/':

Name                          Size (bytes)  Last Modified
------------------------------------------------------------
reports/Q1-2025.pdf              245,120    2025-03-31 14:22:00 UTC
reports/Q2-2025.pdf              312,448    2025-06-30 09:15:00 UTC
reports/annual-2024.xlsx          98,304    2025-01-15 11:00:00 UTC

3 object(s) found.
```

---

### `read_pdf`

Extract text and tables from a PDF file. Table structure is preserved — row labels stay aligned with their values. This is essential for financial statements.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | string | Yes | Path to the PDF file, e.g. `reports/Q4-2025.pdf` |

**Example usage in Claude:**
> *"Read reports/Q4-2025.pdf and extract the income statement"*

**Note on complex PDFs:** Multi-column financial tables are extracted with column alignment preserved. However, heavily image-based PDFs (scanned documents) may yield limited text — the PDF must contain actual text, not just images.

---

### `read_spreadsheet`

Read an Excel (.xlsx) workbook and return computed cell values. Formulas are evaluated — you get the result, not the formula string.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | — | Path to the .xlsx file |
| `sheet_name` | string | No | `null` | Specific sheet name. If omitted, all sheets are returned. |

**Example usage in Claude:**
> *"Read the actuals tab from reports/budget-2025.xlsx"*

**Important limitation:** `data_only` mode in openpyxl reads cached values stored by Excel. If the file was created programmatically and never opened and saved in Excel, formula cells may return empty. Files saved by Excel itself always work correctly.

---

### `read_file`

Read a text-based file — JSON, CSV, or plain text.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | string | Yes | Path to the file, e.g. `data/metrics.json` |

JSON files are automatically pretty-printed. CSV and .txt files are returned as-is.

**Example usage in Claude:**
> *"Read the file data/metrics.json"*

---

### `write_file`

Write a text or JSON file to storage. Creates the file if it does not exist; overwrites it if it does.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | string | Yes | Destination path, e.g. `outputs/result.json` |
| `content` | string | Yes | Text content to write |

JSON content is automatically detected and pretty-printed before saving.

**Example usage in Claude:**
> *"Save the analysis results to outputs/q4-summary.json"*

---

### `create_spreadsheet`

Create an Excel (.xlsx) spreadsheet from data and save it to storage.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | — | Destination path, e.g. `outputs/report.xlsx` |
| `data` | string | Yes | — | JSON-encoded table data (see below) |
| `sheet_name` | string | No | `"Sheet1"` | Name of the worksheet |

**Data format — list of dicts** (keys become column headers):
```json
[
  {"Company": "Acme", "Revenue": 1200000, "EBITDA": 240000},
  {"Company": "Beta", "Revenue": 850000,  "EBITDA": 127500}
]
```

**Data format — list of lists** (first row can be headers):
```json
[
  ["Company", "Revenue", "EBITDA"],
  ["Acme", 1200000, 240000],
  ["Beta", 850000, 127500]
]
```

**Example usage in Claude:**
> *"Create a spreadsheet at outputs/summary.xlsx with the revenue figures"*

---

### `create_word_document`

Create a Word (.docx) document from text content and save it to storage.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | string | Yes | Destination path, e.g. `outputs/report.docx` |
| `content` | string | Yes | Document content (see heading syntax below) |

**Heading syntax:**

| Syntax | Result |
|---|---|
| `# Title` | Heading 1 |
| `## Section` | Heading 2 |
| `### Subsection` | Heading 3 |
| Blank line | Paragraph break |
| Anything else | Normal paragraph |

**Example usage in Claude:**
> *"Generate a Word report and save it to outputs/Q4-report.docx"*

---

## 9. Workflow Tools Reference

These three tools are **placeholder shells**. They are visible to Claude and can be called, but return placeholder responses until you implement the logic inside `tools/workflows.py`.

See [Adding Your Workflow Logic](#12-adding-your-workflow-logic) for how to fill them in.

---

### `run_financial_analysis`

Run a financial analysis on a document stored in cloud storage.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `document_path` | string | Yes | — | Path to the source document (PDF or XLSX) |
| `analysis_type` | string | No | `"full"` | Type of analysis: `full`, `profitability`, `liquidity`, `solvency`, `growth` |

---

### `generate_report`

Generate a formatted financial report from a source document and save it to storage.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `input_path` | string | Yes | — | Path to the source document |
| `output_path` | string | Yes | — | Where to save the generated report |
| `report_type` | string | No | `"summary"` | Report style: `summary`, `detailed`, `dashboard` |

---

### `compare_documents`

Compare two financial documents and return a structured variance summary.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path_a` | string | Yes | First document (e.g. prior period) |
| `path_b` | string | Yes | Second document (e.g. current period) |

---

## 10. Deploying with Docker

The included `Dockerfile` packages the server for deployment on any container platform (AWS ECS, Google Cloud Run, Fly.io, a VPS, etc.).

### Build the image

```bash
docker build -t financial-mcp-server .
```

### Run the container

```bash
docker run -d \
  --name financial-mcp \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/clients.json:/app/clients.json \
  financial-mcp-server
```

The `-v` flag mounts `clients.json` from your host into the container. This means you can edit `clients.json` on the host and the running container picks up changes immediately — no rebuild needed.

### Environment variables at runtime

Instead of `--env-file`, you can pass individual variables:

```bash
docker run -d \
  -p 8000:8000 \
  -e S3_ENDPOINT_URL=https://... \
  -e S3_ACCESS_KEY=... \
  -e S3_SECRET_KEY=... \
  -e S3_BUCKET_NAME=... \
  -v $(pwd)/clients.json:/app/clients.json \
  financial-mcp-server
```

### Exposing over HTTPS

For production, place the container behind a reverse proxy (nginx, Caddy, Traefik) with a TLS certificate. Clients should always connect over HTTPS, not plain HTTP, since their API key travels in the URL.

---

## 11. Testing the Server

### Health check

Verify the server is running:

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

### Auth layer tests

No key — should return 401:
```bash
curl http://localhost:8000/mcp
# Expected: {"error": "API key required..."}
```

Unknown key — should return 401:
```bash
curl "http://localhost:8000/mcp?api_key=INVALID_KEY"
# Expected: {"error": "API key not recognised..."}
```

Inactive client — should return 401:
```bash
curl "http://localhost:8000/mcp?api_key=KEY_OF_INACTIVE_CLIENT"
# Expected: {"error": "Your access has been deactivated..."}
```

### Testing tools with MCP Inspector

The MCP Inspector is a browser-based tool for calling MCP tools directly, without Claude.

```bash
npx @modelcontextprotocol/inspector
```

When it opens:
1. Set transport to **Streamable HTTP**
2. Set URL to `http://localhost:8000/mcp?api_key=YOUR_TEST_KEY`
3. Click **Connect**
4. All 10 tools appear in the left panel
5. Click a tool, fill in parameters, click **Run**

This lets you verify each tool works correctly before involving Claude.

---

## 12. Adding Your Workflow Logic

Open `tools/workflows.py`. Each workflow tool is a Python async function with a `# TODO` comment where the logic goes.

**Example — implementing `run_financial_analysis`:**

```python
@mcp.tool()
async def run_financial_analysis(
    document_path: str,
    analysis_type: str = "full",
) -> str:
    """..."""
    from storage.client import StorageClient
    from auth.context import client_folder

    client = StorageClient()
    folder = client_folder.get() or ""
    scoped_path = f"{folder}/{document_path}".lstrip("/")

    raw = client.get_object(scoped_path)

    # --- Your proprietary logic goes here ---
    # e.g. parse the document, run calculations, call an internal API
    result = your_analysis_engine.run(raw, analysis_type)
    # ----------------------------------------

    return result
```

The workflow tools follow the same folder-scoping pattern as the storage tools. Use `client_folder.get()` to get the current client's folder prefix, and prepend it to any paths you access.

**Important:** The contents of `tools/workflows.py` are never exposed to clients. They see only the tool name, parameter names, and the string you return.

---

## 13. Security Model

### API key authentication

Every request to the MCP server must include a valid API key as a URL query parameter:

```
https://your-server.com/mcp?api_key=CLIENT_KEY
```

Requests without a key, with an unknown key, or with an inactive key are rejected with HTTP 401 before any tool code runs.

### Folder isolation

Each client is scoped to their own folder in Filestash. The scoping is enforced server-side on every storage operation — clients cannot read or write files outside their folder. Path traversal attempts (e.g. `../../other-client/file.pdf`) are sanitised automatically.

### Code confidentiality

Clients connect to a URL and receive tool results. They have no visibility into:
- Your server code or business logic
- Other clients' data or folder names
- Your Filestash credentials
- The internal structure of your workflows

### Recommendations for production

- Serve over **HTTPS only** — API keys travel in the URL
- Use a **long, random API key** per client (minimum 32 hex characters): `openssl rand -hex 32`
- Do not commit `.env` or `clients.json` with real keys to version control
- Rotate keys if a client's key is ever compromised — add a new entry, deactivate the old one
- Keep `clients.json` outside the Docker image and mount it as a volume so key changes don't require a rebuild

---

## 14. Troubleshooting

**Server won't start — `ModuleNotFoundError`**
Run `pip install -r requirements.txt` and ensure you are using Python 3.12+.

**`data_only` spreadsheet cells return empty**
The Excel file was created programmatically and never opened and re-saved in Excel. openpyxl's `data_only` mode reads cached values written by Excel — if there are none, cells appear empty. Ask the client to open and save the file in Excel once, or generate the file with pre-computed values (no formulas).

**Filestash connection errors**
- Verify `S3_ENDPOINT_URL` ends with `/api/s3` (exact path depends on your Filestash version)
- Confirm the access key and secret are correct
- The server uses path-style addressing — ensure your Filestash instance supports it

**Client gets "API key not recognised"**
- Check the key in `clients.json` exactly matches what was sent to the client (case-sensitive)
- Ensure `clients.json` is valid JSON (no trailing commas)

**Client gets "Your access has been deactivated"**
The client's `active` field in `clients.json` is `false`. Set it to `true` to restore access.

**Tool results look wrong in Claude**
Use MCP Inspector to call the tool directly and inspect the raw output. This bypasses Claude and shows exactly what the tool returns.

**PDF tables are not aligned correctly**
pdfplumber works well on digitally-created PDFs. Scanned PDFs (images of documents) produce no text at all — the PDF must contain actual embedded text. For scanned documents, an OCR step would need to be added before passing to pdfplumber.
