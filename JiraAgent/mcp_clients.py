from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

client = MultiServerMCPClient({
    "jira": {
        "command": "docker",
        "args": [
            "run", "-i", "--rm",
            "--env-file", ".env",
            "ghcr.io/sooperset/mcp-atlassian:latest"
        ],
        "transport": "stdio"
    }
})

async def get_tools():
    return await client.get_tools()


if __name__ == "__main__":
    try:
        tools = asyncio.run(get_tools())
        print("Available Jira Tools:")
        for t in tools:
            print("-", t.name)
    except Exception as e:
        print("Error:", e)
