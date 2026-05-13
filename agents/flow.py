# agents/flow.py

from __future__ import annotations

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from .schema import IntakeState

from .extract import node_extract

from .nodes import (
    node_ensure_problem,
    node_ensure_returning,
    node_ensure_doctor,
    node_ensure_date,
    node_fetch_slots,
    node_book_appointment,
    node_await_slot_selection,
)


# =========================================================
# ROUTING HELPERS
# =========================================================

def _route_from_start(state: IntakeState) -> str:
    """
    Entry-point router — runs BEFORE extract.

    Critical guard: if we are already waiting for slot selection
    (next_step == 'select_slot'), we must NOT pass the user message
    through node_extract.  Doing so risks:

      • duplicate DB queries (slots re-fetched every turn)
      • the extract node misreading "slot 2" as a symptom or date

    Instead we branch immediately:
      - selected_slot_id present → book_appointment
      - no selected_slot_id      → await_slot  (re-prompt, no DB hit)

    For all other states, proceed normally to extract.
    """
    next_step = state.get("next_step")

    if next_step == "select_slot":
        if state.get("selected_slot_id"):
            return "book_appointment"
        return "await_slot"

    return "extract"


def _route_after_extract(state: IntakeState) -> str:
    """
    After extraction, route to whichever piece of information is
    still missing, in order of priority.

    Full happy path:
      extract → ensure_problem
              → ensure_returning
              → ensure_doctor
              → ensure_date
              → fetch_slots          ← sets next_step='select_slot', END
      (next request)
              → book_appointment     ← selected_slot_id present, END
    """
    p = state.get("patient")
    if not p:
        return "ensure_problem"

    if not p.problem or not p.problem_description:
        return "ensure_problem"

    if p.returning_patient is None:
        return "ensure_returning"

    if not p.doctor:
        return "ensure_doctor"

    if not p.appointment_date:
        return "ensure_date"

    # All required fields collected.
    # selected_slot_id check here is a safety net — normally the start
    # router handles this case before extract ever runs.
    if state.get("selected_slot_id"):
        return "book_appointment"

    return "fetch_slots"


def _route_after_ensure(state: IntakeState) -> str:
    """
    After any ensure-* node, re-check whether that node set a message
    (still waiting for user input) or whether we can move to the next check.
    """
    if state.get("message"):
        return END  # waiting for user reply

    p = state.get("patient")
    if not p:
        return END

    if not p.problem or not p.problem_description:
        return "ensure_problem"

    if p.returning_patient is None:
        return "ensure_returning"

    if not p.doctor:
        return "ensure_doctor"

    if not p.appointment_date:
        return "ensure_date"

    # All fields present
    if state.get("selected_slot_id"):
        return "book_appointment"

    return "fetch_slots"


# =========================================================
# BUILD GRAPH
# =========================================================

def _build_graph():

    g = StateGraph(IntakeState)

    # ----------------------------------------------------------
    # Nodes
    # ----------------------------------------------------------

    g.add_node("extract",          node_extract)
    g.add_node("ensure_problem",   node_ensure_problem)
    g.add_node("ensure_returning", node_ensure_returning)
    g.add_node("ensure_doctor",    node_ensure_doctor)
    g.add_node("ensure_date",      node_ensure_date)
    g.add_node("fetch_slots",      node_fetch_slots)
    g.add_node("await_slot",       node_await_slot_selection)
    g.add_node("book_appointment", node_book_appointment)

    # ----------------------------------------------------------
    # Entry point — check session phase BEFORE extract
    # ----------------------------------------------------------

    g.add_conditional_edges(
        START,
        _route_from_start,
        {
            "extract":          "extract",
            "await_slot":       "await_slot",
            "book_appointment": "book_appointment",
        },
    )

    # ----------------------------------------------------------
    # After extraction → route to first missing field or slots
    # ----------------------------------------------------------

    g.add_conditional_edges(
        "extract",
        _route_after_extract,
        {
            "ensure_problem":   "ensure_problem",
            "ensure_returning": "ensure_returning",
            "ensure_doctor":    "ensure_doctor",
            "ensure_date":      "ensure_date",
            "fetch_slots":      "fetch_slots",
            "book_appointment": "book_appointment",
        },
    )

    # ----------------------------------------------------------
    # After each ensure node → next missing field or END
    # ----------------------------------------------------------

    _ensure_targets = {
        "ensure_problem":   "ensure_problem",
        "ensure_returning": "ensure_returning",
        "ensure_doctor":    "ensure_doctor",
        "ensure_date":      "ensure_date",
        "fetch_slots":      "fetch_slots",
        "book_appointment": "book_appointment",
        END:                END,
    }

    for node_name in (
        "ensure_problem",
        "ensure_returning",
        "ensure_doctor",
        "ensure_date",
    ):
        g.add_conditional_edges(
            node_name,
            _route_after_ensure,
            _ensure_targets,
        )

    # ----------------------------------------------------------
    # Terminal edges
    # fetch_slots → END   : frontend shows slots and waits
    # await_slot  → END   : re-prompt, no DB hit, still waiting
    # book_appointment → END : booking confirmed
    # ----------------------------------------------------------

    g.add_edge("fetch_slots",      END)
    g.add_edge("await_slot",       END)
    g.add_edge("book_appointment", END)

    return g.compile()


# =========================================================
# GRAPH INSTANCE
# =========================================================

intake_graph = _build_graph()