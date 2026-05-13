from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from agents import (
    intake_graph,
    PatientIntake,
)

from api import get_routers

from api.utils import (
    patient_to_dict,
    dict_to_patient,
    get_ip_address,
)

from api.state import (
    SESSION_STORE,
    touch_session,
    purge_expired_sessions,
)

from api.dependencies import get_current_user


# =========================================================
# LOGGING
# =========================================================
# Use Python's stdlib logger instead of bare print() / traceback.print_exc().
# In production, swap the handler for a JSON formatter + CloudWatch/Datadog.
# TODO (production / Issue 4): move to structured logging (e.g. structlog or
#   python-json-logger) so log lines are machine-parseable and carry
#   request IDs, user IDs, and trace context.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("medical_api")


# =========================================================
# BACKGROUND TASK — session cleanup
# =========================================================

# How often (seconds) the cleanup coroutine wakes up.
_CLEANUP_INTERVAL_SECONDS = 30 * 60  # every 30 minutes


async def _session_cleanup_loop() -> None:
    """
    Periodically purge sessions that have been inactive for longer than
    SESSION_TTL_SECONDS (4 hours).  Runs as a background asyncio task
    for the lifetime of the server process.

    TODO (production / Issue 2): remove this coroutine once SESSION_STORE
    is replaced with Redis — TTL expiry will be handled by Redis itself.
    """
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
        removed = purge_expired_sessions()
        if removed:
            logger.info("Session cleanup: removed %d expired session(s).", removed)


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──────────────────────────────────────────
    logger.info("=== ROUTES ===")
    for route in app.router.routes:
        methods = ",".join(sorted(route.methods or []))
        logger.info("  %-10s %s", methods, route.path)
    logger.info("================")

    # Start the session-cleanup background task
    cleanup_task = asyncio.create_task(_session_cleanup_loop())
    logger.info("Session cleanup task started (interval=%ds).", _CLEANUP_INTERVAL_SECONDS)

    yield

    # ── shutdown ─────────────────────────────────────────
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Session cleanup task stopped.")


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="AI Medical Scheduling API",
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

# TODO (production / Issue 3):
#   Replace allow_origins=["*"] with the exact frontend domain, e.g.:
#     allow_origins=["https://your-app.vercel.app"]
#   Wide-open CORS is fine for local development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DEV ONLY — tighten before deploying
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO (production / Issue 5 — rate limiting):
#   Add SlowAPI or similar to prevent spam / token flooding, e.g.:
#     from slowapi import Limiter
#     limiter = Limiter(key_func=get_remote_address)
#     @app.post("/chat")
#     @limiter.limit("20/minute")
#     async def chat(...): ...

# TODO (production / Issue 6 — request IDs):
#   @app.middleware("http")
#   async def add_request_id(request, call_next):
#       request_id = str(uuid.uuid4())
#       token = _request_id_ctx.set(request_id)
#       response = await call_next(request)
#       response.headers["X-Request-ID"] = request_id
#       _request_id_ctx.reset(token)
#       return response


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():
    return {
        "ok": True,
        "app": "AI Medical Scheduling API",
        "sessions_active": len(SESSION_STORE),
    }


# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    """
    POST /chat request body.

    Medical / symptom data must never travel in URL query strings.

    Turn-by-turn contract:
    ┌─────────────────────────────────────────────────────────┐
    │ Turns 1..N   { "message": "I have a fever" }            │
    │                                                         │
    │ Slot fetch   → API replies with next_step='select_slot' │
    │                and available_slots=[{slot_id, start,    │
    │                end}, ...]                               │
    │                                                         │
    │ Book turn    { "message": "I'll take slot 1",           │
    │               "selected_slot_id": 12 }                  │
    └─────────────────────────────────────────────────────────┘
    """

    message: str
    thread_id: str | None = None
    selected_slot_id: int | None = None  # set when user picks a slot

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("message must not be empty or whitespace")
        return stripped


# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
async def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Main conversational endpoint.

    Accepts a JSON body so that symptom/medical data never appears in
    URL query strings, server logs, or browser history.
    """

    user_id = current_user["user_id"]

    # ----------------------------------------------------------
    # Derive thread_id
    # ----------------------------------------------------------

    # TODO (production / Issue 5):
    #   Let the frontend generate a unique UUID per conversation, e.g.:
    #     thread_id = "chat_" + uuid4().hex
    #   Falling back to f"user-{user_id}" means one active conversation
    #   per user — opening a second tab or starting a new appointment
    #   will corrupt the existing session.  Acceptable for MVP.
    thread_id = (body.thread_id or "").strip() or f"user-{user_id}"

    logger.info(
        "chat | user_id=%s thread_id=%s step=%s slot_id=%s",
        user_id,
        thread_id,
        None,  # will be logged after session load
        body.selected_slot_id,
    )

    # ----------------------------------------------------------
    # SESSION
    # ----------------------------------------------------------

    session = SESSION_STORE.setdefault(
        thread_id,
        {
            "patient": PatientIntake(),
            "next_step": None,
            "booking_done": False,
            "_last_active": 0,   # will be updated by touch_session below
        },
    )

    # Refresh TTL on every interaction
    touch_session(thread_id)

    patient: PatientIntake = session["patient"]
    current_step = session.get("next_step")

    logger.info(
        "chat | thread_id=%s current_step=%s",
        thread_id,
        current_step,
    )

    # ----------------------------------------------------------
    # GRAPH INPUT STATE
    # ----------------------------------------------------------

    state = {
        "input_text": body.message,
        "patient": patient,
        "next_step": current_step,
        "booking_done": session.get("booking_done", False),
        "user_id": user_id,
        "thread_id": thread_id,
        # Forward selected_slot_id when the user has picked a slot;
        # _route_from_start in flow.py routes this to book_appointment
        # WITHOUT passing through node_extract first.
        "selected_slot_id": body.selected_slot_id,
    }

    # ----------------------------------------------------------
    # INVOKE GRAPH
    # ----------------------------------------------------------

    try:
        result = intake_graph.invoke(state)

    except Exception as exc:
        logger.exception(
            "Graph error | thread_id=%s step=%s error=%s",
            thread_id,
            current_step,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {exc}",
        )

    # ----------------------------------------------------------
    # PERSIST SESSION
    # ----------------------------------------------------------

    new_patient = result.get("patient")

    if new_patient is not None:
        try:
            session["patient"] = (
                new_patient
                if isinstance(new_patient, PatientIntake)
                else dict_to_patient(new_patient)
            )
        except Exception:
            pass

    new_step = result.get("next_step")
    session["next_step"] = new_step

    logger.info(
        "chat | thread_id=%s next_step=%s appointment_id=%s",
        thread_id,
        new_step,
        result.get("appointment_id"),
    )

    # ----------------------------------------------------------
    # RESPONSE
    # ----------------------------------------------------------

    message = (
        result.get("message")
        or result.get("reply")
        or "Okay."
    )

    response: dict = {
        "message": message,
        "data": patient_to_dict(session.get("patient")),
        "next_step": new_step,
    }

    # Include slots when the graph has fetched them
    if result.get("available_slots"):
        response["available_slots"] = result["available_slots"]

    # Include appointment id when booking is confirmed
    if result.get("appointment_id"):
        response["appointment_id"] = result["appointment_id"]

    return response


# =========================================================
# REGISTER ROUTERS
# =========================================================

for router in get_routers():
    app.include_router(router)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    import uvicorn

    host_ip = "0.0.0.0"
    port = int(os.getenv("PORT", "5000"))

    logger.info("Server starting on http://localhost:%d", port)
    logger.info("Network URL: http://%s:%d", get_ip_address(), port)
    logger.info("API Docs:    http://%s:%d/docs", get_ip_address(), port)

    uvicorn.run(
    "fastapi_app:app",
    host="0.0.0.0",
    port=5000,
    reload=False,
)