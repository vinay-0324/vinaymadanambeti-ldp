import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from agents.data_jsonformat_agent import data_jsonformat_agent
from agents.query_interpretation_agent import query_interpretation_agent
from agents.data_retrieval_agent import jira_data_node
from agents.summary_agent import summary_agent


class GraphState(TypedDict):
    user_input: str
    structured_query: dict
    jira_result: str
    json_data: list 
    final_summary: str



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


app = graph.compile()


async def run_query_async():
    user_text = input("Enter the Query:")
    result = await app.ainvoke({"user_input": user_text})

    print("\n Structured Query:")
    print(result["structured_query"])

    print("\n Jira API Response:")
    print(result["jira_result"])

    print("\n Json format:")
    print(result["json_data"])

    print("\nFinal Summary:")
    print(result["final_summary"])


def run_query():
    asyncio.run(run_query_async())


if __name__ == "__main__":
    run_query()