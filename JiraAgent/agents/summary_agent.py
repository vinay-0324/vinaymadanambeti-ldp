from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

def summary_agent(state):
    """
    Takes JSON data from data_jsonformat_agent (NOT markdown).
    Converts it into a readable summary.
    Also outputs the JSON table again as markdown.
    Returns: {"final_summary": "..."}
    """
    json_list = state["json_data"]    

    prompt = f"""
You are a Sprint Summary Agent.

Input JSON Data:
{json_list}

Task:
1. Interpret the JSON list which contains sprint metrics.
2. Generate a clear summary paragraph:
   - number of sprints
   - issues included
   - patterns or insights
3. Convert the JSON into a Markdown table.
4. Output MUST be pure Markdown:
   - First, the summary paragraph
   - Below it, the markdown table from the JSON
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    if isinstance(content, list):
        content = "\n".join(
            item["text"] if isinstance(item, dict) and "text" in item else str(item)
            for item in content
        )

    final_text = content.strip()

    return {"final_summary": final_text}
