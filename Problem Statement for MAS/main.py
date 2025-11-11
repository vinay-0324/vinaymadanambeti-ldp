import json
import asyncio
from langgraph.graph import StateGraph, START, END
from agents.data_ingestion_agent import data_ingestion_node
from agents.formulaic_calc_agent import formulaic_calc_agent
from agents.risk_assessment_agent import risk_assessment_node
from agents.report_generation_agent import report_generation_agent
from typing import TypedDict, Annotated

class State(TypedDict, total=False):
    clean_portfolio_data: list
    hist_returns: dict
    calculated_metrics: dict
    routing_decision: str
    validation_log: str

graph_builder = StateGraph(state_schema=State)

graph_builder.add_node("DIA", data_ingestion_node)
graph_builder.add_node("FCA", formulaic_calc_agent)
graph_builder.add_node("RARA", risk_assessment_node)
graph_builder.add_node("RGA", report_generation_agent)

graph_builder.add_edge(START, "DIA")
graph_builder.add_edge("DIA", "FCA")
graph_builder.add_edge("FCA", "RARA")
graph_builder.add_conditional_edges(
    "RARA",
    lambda state: state["routing_decision"],
    {
        "CLEAR": "RGA",   
        "BREACH": END     
    }
)
graph_builder.add_edge("RGA", END)

graph = graph_builder.compile()

async def main():
    final_state = await graph.ainvoke({})
    print("\n Final Computed State:")
    print(json.dumps(final_state, indent=2))



if __name__ == "__main__":
    asyncio.run(main())
