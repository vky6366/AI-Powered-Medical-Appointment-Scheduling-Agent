# agents/flow.py
from __future__ import annotations
from langgraph.graph import StateGraph, START, END

from .schema import IntakeState
from .extract import node_extract
from .nodes import (
    node_ensure_problem,
    node_ask_returning,
    node_ensure_doctor,
    node_ensure_date,
    node_ensure_contact,
    node_ensure_insurance,
    node_finalize,
)

# ...imports unchanged...

def _build_graph():
    g = StateGraph(IntakeState)
    g.add_node("extract", node_extract)
    g.add_node("ensure_problem", node_ensure_problem)
    g.add_node("ask_returning", node_ask_returning)
    g.add_node("ensure_doctor", node_ensure_doctor)
    g.add_node("ensure_date", node_ensure_date)
    g.add_node("ensure_contact", node_ensure_contact)
    g.add_node("finalize", node_finalize)
    g.add_node("ensure_insurance", node_ensure_insurance)   # <— moved after finalize

    g.add_edge(START, "extract")
    g.add_edge("extract", "ensure_problem")
    g.add_edge("ensure_problem", "ask_returning")
    g.add_edge("ask_returning", "ensure_doctor")
    g.add_edge("ensure_doctor", "ensure_date")
    g.add_edge("ensure_date", "ensure_contact")
    g.add_edge("ensure_contact", "finalize")
    g.add_edge("finalize", "ensure_insurance")              # <— runs post-finalize
    g.add_edge("ensure_insurance", END)
    return g.compile()


intake_graph = _build_graph()

