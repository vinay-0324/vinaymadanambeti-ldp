import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import json
from dotenv import load_dotenv

load_dotenv()
formatter_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.getenv("GEMINI_API_KEY")
)


def data_jsonformat_agent(state):
    """
    Convert markdown table string into JSON format.
    """
    markdown_table = state["jira_result"]

    prompt = f"""
You are a data formatting agent.

The following input is a **markdown table** generated from Jira issues.
Convert the table into a **valid JSON array** of objects.

Rules:
- Keys: use column headers exactly as-is.
- Values: keep the same text.
- Dates: keep raw (no formatting).
- Story Points: convert 'N/A' to null.
- Return **ONLY JSON**, no markdown, no explanation.

Markdown Table:
{markdown_table}
"""

    response = formatter_llm.invoke([HumanMessage(content=prompt)])
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item["text"] if isinstance(item, dict) and "text" in item else str(item)
            for item in content
        )

    json_text = content.strip()

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        cleaned = json_text[json_text.find("["): json_text.rfind("]") + 1]
        parsed = json.loads(cleaned)

    return {"json_data": parsed}
