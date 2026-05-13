# Updated `streamlit_app.py`
from __future__ import annotations

import os
import uuid
from typing import Dict, Any, List

import requests
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://localhost:5000"
)


# =========================================================
# STREAMLIT PAGE
# =========================================================

st.set_page_config(
    page_title="RagaAI – Medical Scheduling Assistant",
    page_icon="🩺",
    layout="centered",
)

st.title("🩺 RagaAI – Medical Scheduling Assistant")


# =========================================================
# SESSION STATE
# =========================================================

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = os.getenv(
        "DEMO_TOKEN",
        ""
    )

if "available_slots" not in st.session_state:
    st.session_state["available_slots"] = []

if "next_step" not in st.session_state:
    st.session_state["next_step"] = None


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🔐 Authentication")

    token = st.text_input(
        "JWT Token",
        value=st.session_state["auth_token"],
        type="password",
        help="Paste the JWT returned from /auth/google"
    )

    st.session_state["auth_token"] = token

    if token:
        st.success("JWT token loaded")
    else:
        st.warning("No JWT token set")

    st.divider()

    if st.button("🆕 New Conversation"):

        st.session_state["thread_id"] = str(uuid.uuid4())
        st.session_state["messages"] = []
        st.session_state["available_slots"] = []
        st.session_state["next_step"] = None

        st.rerun()


# =========================================================
# HELPERS
# =========================================================


def get_headers() -> Dict[str, str]:

    token = st.session_state.get(
        "auth_token",
        ""
    )

    headers = {
        "Content-Type": "application/json"
    }

    if token:
        headers[
            "Authorization"
        ] = f"Bearer {token}"

    return headers



def call_chat(
    message: str,
    selected_slot_id: int | None = None,
):

    payload = {
        "message": message,
        "thread_id": st.session_state[
            "thread_id"
        ],
    }

    if selected_slot_id is not None:
        payload[
            "selected_slot_id"
        ] = selected_slot_id

    response = requests.post(
        f"{FASTAPI_URL}/chat",
        json=payload,
        headers=get_headers(),
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# CHAT HISTORY
# =========================================================

for msg in st.session_state["messages"]:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# =========================================================
# USER INPUT
# =========================================================

prompt = st.chat_input(
    "Describe your symptoms..."
)

if prompt:

    st.session_state["messages"].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    try:

        data = call_chat(prompt)

        ai_message = data.get(
            "message",
            "Okay."
        )

        st.session_state[
            "available_slots"
        ] = data.get(
            "available_slots",
            []
        )

        st.session_state[
            "next_step"
        ] = data.get(
            "next_step"
        )

    except Exception as e:

        ai_message = (
            f"⚠️ Backend Error:\n\n{e}"
        )

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": ai_message,
        }
    )

    with st.chat_message("assistant"):
        st.markdown(ai_message)


# =========================================================
# SLOT SELECTION UI
# =========================================================

slots: List[Dict[str, Any]] = (
    st.session_state.get(
        "available_slots",
        []
    )
)

if slots:

    st.divider()

    st.subheader("🗓️ Available Slots")

    for slot in slots:

        slot_id = slot["slot_id"]

        label = (
            f"{slot['start']} → {slot['end']}"
        )

        col1, col2 = st.columns([5, 1])

        with col1:
            st.markdown(label)

        with col2:

            if st.button(
                "Book",
                key=f"slot_{slot_id}"
            ):

                try:

                    data = call_chat(
                        message="book this slot",
                        selected_slot_id=slot_id,
                    )

                    confirmation = data.get(
                        "message",
                        "Appointment booked."
                    )

                    st.session_state[
                        "messages"
                    ].append(
                        {
                            "role": "assistant",
                            "content": confirmation,
                        }
                    )

                    st.session_state[
                        "available_slots"
                    ] = []

                    st.session_state[
                        "next_step"
                    ] = "done"

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Booking failed: {e}"
                    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Built with FastAPI + LangGraph + PostgreSQL + Streamlit"
)
