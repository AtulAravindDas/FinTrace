import yfinance as yf
import pandas as pd
from fastmcp import FastMCP

mcp = FastMCP("FinTrace MCP")

@mcp.tool()
async def get_financial_health(ticker: str) -> dict:
    """
    Fetches comprehensive financial ratios, liquidity, and solvency data 
    for a given ticker using Yahoo Finance.
    """
    ticker_obj = yf.Ticker(ticker.upper())
    info = ticker_obj.info
    
    # We modularize the ratio extraction logic from your FMPDataExtractor
    ratios = {
        "Ticker": ticker.upper(),
        "P/E Ratio": info.get("trailingPE"),
        "Current Ratio": info.get("currentRatio"),
        "Quick Ratio": info.get("quickRatio"),
        "Debt-to-Equity": info.get("debtToEquity"),
        "Free Cash Flow": info.get("freeCashflow"),
        "Beta": info.get("beta"),
        "Revenue Growth (%)": info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else None,
    }

    # Add the descriptive context your Agent needs to audit
    context = {
        "company_name": info.get("longName", "N/A"),
        "industry": info.get("industry", "N/A"),
        "description": info.get("longBusinessSummary", "N/A"),
        "ratios": ratios
    }
    
    return context

if __name__ == "__main__":
    mcp.run()