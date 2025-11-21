import streamlit as st
import asyncio
from langgraph.graph import StateGraph, START, END
from agents.query_interpretation_agent import query_interpretation_agent
from agents.data_retrieval_agent import jira_data_node
from agents.data_jsonformat_agent import data_jsonformat_agent
from agents.summary_agent import summary_agent   
from typing import TypedDict, List, Dict, Any

class GraphState(TypedDict, total=False):
    user_input: str
    structured_query: dict
    jira_result: str
    json_data: List[Dict[str, Any]]
    final_summary: str
 
def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("QIA", query_interpretation_agent)
    graph.add_node("DRA", jira_data_node)
    graph.add_node("JSONFA", data_jsonformat_agent)
    graph.add_node("SUMMARY", summary_agent)

    graph.add_edge(START, "QIA")
    graph.add_edge("QIA", "DRA")
    graph.add_edge("DRA", "JSONFA")
    graph.add_edge("JSONFA", "SUMMARY")
    graph.add_edge("SUMMARY", END)

    return graph.compile()

app = build_graph()

async def run_pipeline(user_text: str):
    return await app.ainvoke({"user_input": user_text})


st.set_page_config(page_title="Jira Sprint Analyzer", layout="wide")

st.title(" Jira Sprint Summary Generator")
st.write("Enter any Jira query (natural language). The multi-agent graph will process it.")

user_input = st.text_area("Enter your query:", height=100)

if st.button("Run"):
    if not user_input.strip():
        st.warning("Please enter your query.")
    else:
        with st.spinner("Running agents... Please wait."):

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_pipeline(user_input))
            loop.close()

        st.success("Completed!")

        st.subheader("Structured Query")
        st.json(result.get("structured_query", {}))

        st.subheader("Jira API Response")
        st.json(result.get("jira_result", {}))

        st.subheader("JSON Formatted Data")
        st.json(result.get("json_data", []))

        st.subheader("Final Summary")
        st.markdown(result.get("final_summary", ""), unsafe_allow_html=True)
