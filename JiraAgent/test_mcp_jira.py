import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

async def test_mcp_jira():
    # Initialize MCP client for Jira
    client = MultiServerMCPClient({
        "jira": {
            "command": "docker",
            "args": [
                "run",
                "-i", "--rm",
                "-e", f"JIRA_URL={os.getenv('JIRA_URL')}",
                "-e", f"JIRA_USERNAME={os.getenv('JIRA_USERNAME')}",
                "-e", f"JIRA_API_TOKEN={os.getenv('JIRA_API_TOKEN')}",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            "transport": "stdio",
        }
    })

    try:
        print("Fetching MCP tools...")
        tools = await client.get_tools()
        print("Tools available from MCP:", tools)

        # Pick a simple tool (first one) for testing
        test_tool_name = list(tools.keys())[0]
        test_tool = tools[test_tool_name]

        print(f"\nInvoking test tool: {test_tool_name} ...")
        test_input = {"board": "346", "status": "Done"}  # Minimal test input

        response = await test_tool.ainvoke(test_input)
        print("\nMCP Test Response:")
        print(response)

    except Exception as e:
        print("Error during MCP test:", e)

    finally:
        try:
            await client.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_mcp_jira())
