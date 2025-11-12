import asyncio
import json
from typing import TypedDict
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

class State(TypedDict, total=False):
    clean_portfolio_data: list
    hist_returns: dict
    calculated_metrics: dict

async def formulaic_calc_agent(state:State):
    print("[FCA] Starting Value-at-Risk (VaR) calculation via MCP...")

    clean_data = state["clean_portfolio_data"]
    hist_returns = state["hist_returns"]

    client = MultiServerMCPClient(
        {
            "RiskCalc MCP Server": {
                "url": "http://localhost:8000/mcp",
                "transport": "streamable_http",
            }
        }
    )

    async with client.session("RiskCalc MCP Server") as session:
        tools = await load_mcp_tools(session)
        var_tool = next((t for t in tools if t.name == "compute_historical_var"), None)

        if not var_tool:
            raise ValueError("[FCA] compute_historical_var tool not found on MCP server!")

        result = await var_tool.ainvoke({
            "portfolio": clean_data,
            "hist_returns": hist_returns,
            "conf_level": 0.99
        })

        if isinstance(result, str):
            result = json.loads(result)

    state["calculated_metrics"] = result

    print("[FCA] Computation complete\n")
    return state

