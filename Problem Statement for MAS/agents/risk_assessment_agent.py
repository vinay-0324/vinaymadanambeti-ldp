import os
import json
from typing import TypedDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RISK_CONFIG_PATH = os.path.join(DATA_DIR, "risk_config.json")


class State(TypedDict, total=False):
    calculated_metrics: dict
    routing_decision: str
    validation_log: str


def risk_assessment_node(state: State):
    """
    Compares calculated VaR with risk threshold and decides routing.
    """
    print("\n[RARA] Starting Risk Assessment...")

    if not os.path.exists(RISK_CONFIG_PATH):
        raise FileNotFoundError(f"Risk config file not found: {RISK_CONFIG_PATH}")

    with open(RISK_CONFIG_PATH, "r") as f:
        risk_config = json.load(f)

    var_threshold = risk_config.get("VaR_threshold_usd", 550000.0)
    calculated_var = state["calculated_metrics"].get("VaR_99")

    print(f"[RARA] Calculated VaR99: ${calculated_var:,.2f}")
    print(f"[RARA] Config Threshold: ${var_threshold:,.2f}")

    if calculated_var > var_threshold:
        state["routing_decision"] = "BREACH"
        state["validation_log"] = "Manual Review Required (VaR Breach)"
        print("[RARA] Decision: BREACH - Routed to Human-in-the-Loop (HITL)")
    else:
        state["routing_decision"] = "CLEAR"
        state["validation_log"] = "Auto Approved (No Breach)"
        print("[RARA] Decision: CLEAR - Safe to generate report")

    return state
