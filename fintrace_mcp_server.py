import yfinance as yf
import pandas as pd
from fastmcp import FastMCP
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json
from pathlib import Path


mcp = FastMCP("FinTrace MCP")

@mcp.tool()
async def get_financial_health(ticker: str) -> dict:
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        info = ticker_obj.info
        financials = ticker_obj.financials
        balance_sheet = ticker_obj.balance_sheet
        cash_flow = ticker_obj.cashflow
        ratios = {
            "Ticker": ticker.upper(),
            "P/E Ratio": info.get("trailingPE"),
            "P/B Ratio": info.get("priceToBook"),
            "Current Ratio": info.get("currentRatio"),
            "Quick Ratio": info.get("quickRatio"),
            "ROE (%)": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
            "ROA (%)": info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None,
            "Profit Margin (%)": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else None,
            "Operating Margin (%)": info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else None,
            "Net Margin (%)": info.get("netMargins", 0) * 100 if info.get("netMargins") else None,
            "Gross Margin (%)": info.get("grossMargins", 0) * 100 if info.get("grossMargins") else None,
            "EPS": info.get("trailingEps"),
            "Dividend Yield (%)": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
            "Debt-to-Equity": info.get("debtToEquity"),
            "Free Cash Flow": info.get("freeCashflow"),
            "Beta": info.get("beta"),
            "Revenue Growth (%)": info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else None,
            "Interest Coverage Ratio": info.get("interestCoverage", 0) * 100 if info.get("interestCoverage") else None
        }
        try:
            if not financials.empty and len(financials.columns) >= 2:
                
                if "Total Revenue" in financials.index:
                    rev_now = financials.loc["Total Revenue"].iloc[0]
                    rev_prev = financials.loc["Total Revenue"].iloc[1]
                    ratios["Revenue Growth (%)"] = ((rev_now - rev_prev) / abs(rev_prev)) * 100
        except Exception as e:
            print(f"Could not calculate Revenue Growth: {e}")
            ratios["Revenue Growth (%)"] = info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else None
        
        
        try:
            if not balance_sheet.empty:
                if "Total Debt" in balance_sheet.index and "Total Assets" in balance_sheet.index:
                    total_debt = balance_sheet.loc["Total Debt"].iloc[0]
                    total_assets = balance_sheet.loc["Total Assets"].iloc[0]
                    ratios["Debt-to-Asset"] = total_debt / total_assets
        except Exception as e:
            print(f"Could not calculate Debt-to-Asset: {e}")
            ratios["Debt-to-Asset"] = None
        
        
        try:
            if not financials.empty:
                if "EBIT" in financials.index and "Interest Expense" in financials.index:
                    ebit = financials.loc["EBIT"].iloc[0]
                    interest = abs(financials.loc["Interest Expense"].iloc[0])
                    if interest != 0:
                        ratios["Interest Coverage Ratio"] = ebit / interest
        except Exception as e:
            print(f"Could not calculate Interest Coverage: {e}")
            ratios["Interest Coverage Ratio"] = None

    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return {"error": str(e)}

    context = {
        "company_name": info.get("longName", "N/A"),
        "industry": info.get("industry", "N/A"),
        "description": info.get("longBusinessSummary", "N/A"),
        "ratios": ratios
    }
    
    return context

news_cache = {}
CACHE_DURATION = timedelta(minutes=30)

@mcp.tool()
async def get_company_news(ticker: str) -> str:
    """
    Fetches and filters the latest 10 news articles for a company.
    Uses Finnhub for high-quality summaries and source data.
    """
    ticker = ticker.upper()
    api_key = os.getenv('FINNHUB_API_KEY')
    
    if ticker in news_cache:
        cached_time, cached_data = news_cache[ticker]
        if datetime.now() - cached_time < CACHE_DURATION:
            return cached_data

    try:
        
        profile_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={api_key}'
        profile_res = requests.get(profile_url).json()
        company_full_name = profile_res.get('name', ticker)
        
        
        core_name = company_full_name.replace(' Corporation', '').replace(' Corp', '') \
                                     .replace(' Inc.', '').replace(' Inc', '') \
                                     .replace(' Ltd', '').replace(',', '').strip().lower()

        
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        news_url = f'https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start_date}&to={today}&token={api_key}'
        news_data = requests.get(news_url).json()

        
        news_output = []
        count = 0
        
        for article in news_data[:30]: 
            headline = article.get('headline', '')
            summary = article.get('summary', '')
            source = article.get('source', 'Unknown')
            
            
            if ticker.lower() in headline.lower() or core_name in headline.lower():
                count += 1
                formatted_article = (
                    f"[{count}] {headline}\n"
                    f"SOURCE: {source}\n"
                    f"SUMMARY: {summary}\n"
                )
                news_output.append(formatted_article)
                
                if count >= 10: break

        final_result = "\n".join(news_output) if news_output else "No recent relevant news found."
        
        
        news_cache[ticker] = (datetime.now(), final_result)
        
        return final_result

    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"

if __name__ == "__main__":
    mcp.run()