from mcp.server.fastmcp import FastMCP
import uuid

mcp = FastMCP("RiskCalc MCP Server")
@mcp.tool()
async def compute_historical_var(portfolio: list, hist_returns: dict, conf_level: float = 0.99) -> dict:
    """
    Computes Historical Value at Risk (VaR) for the given portfolio using
    10 days of historical returns.
    """

    pnl_distribution = []
    num_days = len(next(iter(hist_returns.values())))

    for day_index in range(num_days):
        daily_pnl = 0.0
        for asset in portfolio:
            asset_id = asset["Asset ID"]
            qty = asset["Quantity"]
            price = asset["Market Price (USD)"]

            if asset_id not in hist_returns:
                print(f"[Warning] No historical returns for asset: {asset_id}")
                continue

            daily_return = hist_returns[asset_id][day_index]
            daily_pnl += qty * price * daily_return

        pnl_distribution.append(daily_pnl)

    pnl_distribution.sort()
    var_index = int((1 - conf_level) * len(pnl_distribution))
    var_99 = abs(pnl_distribution[var_index])

    return {
        "VaR_99": round(var_99, 2),
        "pnl_distribution": [round(x, 2) for x in pnl_distribution],
        "mcp_audit_id": str(uuid.uuid4()),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
