FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the MCP server port
EXPOSE 8000

# FastMCP's streamable-http transport surfaces an ASGI app.
# We run it with uvicorn, pointing at the `app` object in server.py.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
