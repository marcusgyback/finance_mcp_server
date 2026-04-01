"""
tools/workflows.py — Placeholder shells for financial workflow tools.

These tools define the interface (name, parameters, docstring) that Claude sees,
but the actual analysis logic is intentionally left for you to implement.
Replace each `return` statement with real business logic — for example, calls to
an internal analysis engine, LLM chains, or data-processing pipelines.

Call register_tools(mcp) from server.py to attach these tools to the FastMCP
instance, exactly as with the storage tools.
"""

from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP) -> None:
    """Attach all workflow placeholder tools to *mcp*."""

    # ------------------------------------------------------------------
    # Placeholder 1 — run_financial_analysis
    # ------------------------------------------------------------------
    @mcp.tool()
    async def run_financial_analysis(
        document_path: str,
        analysis_type: str = "full",
    ) -> str:
        """Run a financial analysis on a document stored in cloud storage.

        Supported analysis types (once implemented):
            "full"        — comprehensive analysis covering all metrics
            "profitability" — margins, EBITDA, return ratios
            "liquidity"   — current ratio, quick ratio, cash flow
            "solvency"    — debt ratios, interest coverage
            "growth"      — YoY and CAGR calculations

        Args:
            document_path: Storage key of the source document (PDF or XLSX).
            analysis_type: Type of analysis to perform (default: "full").
        """
        # TODO: Implement analysis logic here.
        # Suggested approach:
        #   1. Fetch the document with StorageClient.get_object(document_path)
        #   2. Parse it with read_pdf or read_spreadsheet helpers
        #   3. Run your financial metrics calculations
        #   4. Return a structured results string
        return (
            f"[PLACEHOLDER] run_financial_analysis called with "
            f"document_path='{document_path}', analysis_type='{analysis_type}'. "
            f"Implement the analysis logic in tools/workflows.py."
        )

    # ------------------------------------------------------------------
    # Placeholder 2 — generate_report
    # ------------------------------------------------------------------
    @mcp.tool()
    async def generate_report(
        input_path: str,
        output_path: str,
        report_type: str = "summary",
    ) -> str:
        """Generate a formatted financial report from a source document.

        Reads the input document, applies report formatting, and writes the
        output to storage.  The output format is inferred from the output_path
        extension (.docx, .xlsx, .pdf).

        Supported report types (once implemented):
            "summary"      — one-page executive summary
            "detailed"     — full multi-section report
            "dashboard"    — key metrics in tabular form

        Args:
            input_path:  Storage key of the source document.
            output_path: Storage key where the generated report should be saved.
            report_type: Style of report to generate (default: "summary").
        """
        # TODO: Implement report generation logic here.
        # Suggested approach:
        #   1. Fetch and parse the input document
        #   2. Run any required analysis
        #   3. Use create_word_document or create_spreadsheet to write output
        #   4. Return a confirmation with output_path
        return (
            f"[PLACEHOLDER] generate_report called with "
            f"input_path='{input_path}', output_path='{output_path}', "
            f"report_type='{report_type}'. "
            f"Implement the report generation logic in tools/workflows.py."
        )

    # ------------------------------------------------------------------
    # Placeholder 3 — compare_documents
    # ------------------------------------------------------------------
    @mcp.tool()
    async def compare_documents(path_a: str, path_b: str) -> str:
        """Compare two financial documents and return a structured diff summary.

        Useful for period-over-period comparisons (e.g. Q3 vs Q4 income
        statements) or variance analysis between budget and actuals.

        Args:
            path_a: Storage key of the first document (e.g. prior period).
            path_b: Storage key of the second document (e.g. current period).
        """
        # TODO: Implement comparison logic here.
        # Suggested approach:
        #   1. Fetch and parse both documents
        #   2. Align matching line items or table rows
        #   3. Calculate absolute and percentage variances
        #   4. Return a formatted comparison table
        return (
            f"[PLACEHOLDER] compare_documents called with "
            f"path_a='{path_a}', path_b='{path_b}'. "
            f"Implement the comparison logic in tools/workflows.py."
        )
