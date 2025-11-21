import os
import json
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

async def jira_data_node(state):
    structured_query = state["structured_query"]
    structured_str = json.dumps(structured_query)
    user_query = f"""
Using this structured Jira query:

{structured_str}

Fetch the data from Jira using MCP functions.
Return a **clean Markdown table**:
- Do NOT include JSON, tool calls, or metadata.
- include date 
- Extract Story Points from ANY field (Story Points)
- If present in JSON, include the value


IMPORTANT:
1. Jira stores Story Points in a custom field.
2. Identify the correct field by checking `names` mapping where the value == "Story Points".
3. Extract Story Points using that custom field ID.
"""

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
        tools = await client.get_tools()
        agent = create_agent(model=model, tools=tools)

      
        jira_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_query}]}
        )

        
        content = jira_response["messages"][-1].content

        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                    content = content[0]["text"]

            if isinstance(content, str):
                markdown_output = content
            else:
                markdown_output = str(content)

            return {"jira_result": markdown_output.strip()}


    except Exception as e:
            print(f"DRA Error: {e}")
            return {"jira_result": f"Failed to fetch Jira data: {e}"}

    finally:
            try:
                await client.close()
            except:
                pass

    return {"jira_result": "No Jira data returned"}
