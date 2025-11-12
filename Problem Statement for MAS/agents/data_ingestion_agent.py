import asyncio
import json
import os
from langgraph.graph import StateGraph, START, END

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PORTFOLIO_PATH = os.path.join(DATA_DIR, "portfolio_dump_B.json")
MARKET_CLOSES_PATH = os.path.join(DATA_DIR, "market_closes_B.json")

async def load_json(file_path: str):
    """Loads a JSON file asynchronously and returns the data."""
    await asyncio.sleep(0.1) 
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r") as f:
        return json.load(f)

def data_ingestion_node(state):
    """LangGraph node to load and clean portfolio and market data."""
    result = asyncio.run(_data_ingestion_async())
    state.update(result)
    print(" \n [DIA] Data ingestion completed\n")
    return state

async def _data_ingestion_async():
    """Reads, cleans, and structures portfolio & market data."""
    portfolio_data = await load_json(PORTFOLIO_PATH)
    market_data = await load_json(MARKET_CLOSES_PATH)

    clean_portfolio_data = [
        {
            "Asset ID": item.get("Asset ID", ""),
            "Asset Type": item.get("Asset Type", "Unknown"),
            "Quantity": float(item.get("Quantity", 0)),
            "Market Price (USD)": float(item.get("Market Price (USD)", 0)),
            "Sector": item.get("Sector", "N/A")
        }
        for item in portfolio_data
    ]

    return {
        "clean_portfolio_data": clean_portfolio_data,
        "hist_returns": market_data
    }


