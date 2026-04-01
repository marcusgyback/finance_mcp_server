# Financial Analysis MCP Server

A Model Context Protocol (MCP) server that gives Claude access to financial document tools hosted on your own infrastructure. Clients connect from claude.ai using a custom server URL — the server logic stays hidden, and Claude only sees tool names, parameter descriptions, and results.

The server ships with 7 fully implemented storage tools for reading and writing PDFs, Excel workbooks, Word documents, and plain-text files stored in S3 or any S3-compatible storage (Filestash, MinIO, Backblaze B2). Three financial workflow tool stubs are also included, ready for you to fill in with your own analysis logic.

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd financial-mcp-server
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your storage credentials:

```
S3_ENDPOINT_URL=https://your-filestash-or-s3-endpoint.com
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

For standard AWS S3, leave `S3_ENDPOINT_URL` empty (or remove it from `.env`) and boto3 will use the default AWS endpoints.

---

## Running

### Locally

```bash
python server.py
```

The server starts on `http://0.0.0.0:8000` (or the host/port set in `.env`).

### With Docker

```bash
# Build the image
docker build -t financial-mcp-server .

# Run with your .env file
docker run --env-file .env -p 8000:8000 financial-mcp-server
```

---

## Connecting from claude.ai

1. Open **claude.ai** and go to **Settings → Integrations** (or the MCP / Custom Tools section).
2. Add a **Custom MCP Server**.
3. Enter the URL:
   ```
   http://your-server-host:8000/mcp
   ```
   Replace `your-server-host` with your server's IP address or domain name.  If you are running locally and testing in the browser, use `http://localhost:8000/mcp`.
4. Save. Claude will now list the available tools and can call them during conversations.

> For production use, put the server behind a reverse proxy (nginx, Caddy) with TLS so the URL is `https://`.

---

## Storage Tools Reference

| Tool | Description |
|------|-------------|
| `list_folder` | List files/folders under a storage path prefix with sizes and dates |
| `read_pdf` | Extract text and tables from a PDF; tables are column-aligned |
| `read_spreadsheet` | Read an Excel workbook as CSV text, one section per sheet |
| `read_file` | Read a `.json`, `.csv`, or `.txt` file; JSON is pretty-printed |
| `write_file` | Write text content to a storage path; JSON is auto-formatted |
| `create_spreadsheet` | Create an `.xlsx` file from a JSON array of dicts or lists |
| `create_word_document` | Create a `.docx` from text with `#`/`##`/`###` heading syntax |

### read_pdf — table handling

`read_pdf` uses pdfplumber's `extract_tables()` to capture tabular data separately from paragraph text. Each table is formatted with `str.ljust()` so that row labels stay aligned with their numeric columns — critical for financial statements where misaligned numbers are misleading.

### read_spreadsheet — formula caching note

`read_spreadsheet` opens workbooks with `data_only=True`, which reads cached computed values rather than raw formulas. These cached values are only present if the workbook was opened and saved in Excel (or a compatible app) after the last edit. Files generated programmatically and never opened in Excel may return `None` for formula cells.

---

## Adding Workflow Logic

Open `tools/workflows.py`. Each of the three placeholder tools contains a `# TODO` comment with a suggested implementation approach:

- **`run_financial_analysis`** — fetch a document, parse it, run metric calculations, return structured results.
- **`generate_report`** — read an input document, format it, write output as `.docx` or `.xlsx`.
- **`compare_documents`** — fetch two documents, align line items, compute variances.

The placeholder shells already expose the correct tool names and parameter descriptions to Claude.  Replace the `return "[PLACEHOLDER]..."` line in each function with your real logic.  No changes to `server.py` are needed.
