"""
tools/workflows.py — Protected financial workflow tools.

These tools define the interface (name, parameters, docstring) that Claude sees.
The actual analysis logic is intentionally left for you to implement after delivery.
Clients can call these tools through Claude but cannot inspect the code running
behind them — that is the core value of the MCP server pattern.

Replace each `return` statement with your real business logic.
"""

from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP) -> None:
    """Attach all workflow tools to *mcp*."""

    @mcp.tool()
    async def run_financial_analysis(company_name: str) -> str:
        """Run a proprietary financial analysis for the given company.

        Analyses the company's financial data stored in your folder and returns
        a structured report covering key metrics and indicators.

        Args:
            company_name: The name of the company to analyse.
        """
        # TODO: Replace with your real analysis logic.
        return f"Financial analysis for '{company_name}' — implementation pending."

    @mcp.tool()
    async def generate_report(company_name: str) -> str:
        """Generate a formatted financial report for the given company.

        Reads source documents from your folder, applies proprietary report
        formatting, and returns the completed report.

        Args:
            company_name: The name of the company to generate a report for.
        """
        # TODO: Replace with your real report generation logic.
        return f"Report for '{company_name}' — implementation pending."

    @mcp.tool()
    async def compare_financials(company_name: str) -> str:
        """Compare financial periods for the given company.

        Performs a period-over-period variance analysis using documents stored
        in your folder and returns a structured comparison summary.

        Args:
            company_name: The name of the company to compare financials for.
        """
        # TODO: Replace with your real comparison logic.
        return f"Financial comparison for '{company_name}' — implementation pending."
