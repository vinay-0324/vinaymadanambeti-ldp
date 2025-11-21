import json
from urllib.parse import uses_query
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv 
import os

load_dotenv() 
api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key
)

def query_interpretation_agent(state):
    """Extract structured query from user input using Gemini."""
    user_query = state["user_input"]

    prompt_text = f"""
You are a Jira Query Interpretation Agent. Your job is to convert any natural-language user query into a structured JSON object that can be used to fetch data from Jira.

Rules:
1. Identify what the user wants: sprints, issues, or both. Fill the "metrics" field accordingly.
2. Detect any filters mentioned in the query:
   - Status → populate filters.status
   - Assignee → populate filters.assignee
   - Issue type → populate filters.issue_type
   - Labels → populate filters.labels
3. Identify the board if mentioned. Always fill "board".
4. Identify the sprint if mentioned:
   - If the query refers to “all sprints” or does not specify, fill "sprint": "all".
   - If a specific sprint is mentioned, fill "sprint" with that name or ID.
5. Identify any time range in the query and fill "time_range". If none mentioned, fill as "all".
6. Fill other fields logically if possible; if missing, use null.
7. Output **only valid JSON**, no Markdown or extra text.

Required JSON Schema:
{{
  "intent": "",            
  "project": "",             
  "board": "",               
  "sprint": "",              
  "time_range": "",          
  "metrics": [],             
  "filters": {{
    "status": [],
    "assignee": [],
    "issue_type": [],
    "labels": []
  }},         
  "additional_params": {{}}    
}}

User Query:
{user_query}

Return ONLY valid JSON.
"""

    response = llm.invoke([HumanMessage(content=prompt_text)])
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
        cleaned = json_text[json_text.find("{"): json_text.rfind("}") + 1]
        parsed = json.loads(cleaned)

    return {"structured_query": parsed}
