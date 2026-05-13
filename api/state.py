# api/state.py
from __future__ import annotations

import time
from typing import Any, Dict

# TODO (production / Issue 1 — SESSION_STORE volatility):
#   In-memory dict is perfectly fine for local development.
#   For production you MUST replace this with an external store:
#
#   Option A — Redis (recommended for AWS/cloud):
#     import redis, json
#     r = redis.Redis.from_url(os.environ["REDIS_URL"])
#     # wrap get/set with json.dumps/loads + TTL
#
#   Option B — PostgreSQL conversations table:
#     Store {thread_id, patient_json, next_step, booking_done}
#     via SQLAlchemy, one row per active session.
#
#   Symptoms of not fixing this in prod:
#     • server restart → all sessions lost, users restart mid-flow
#     • multi-instance (auto-scaling) → each pod has its own dict,
#       load balancer sends user to different pod → session gone
#     • reload=True (dev mode) → resets between hot-reloads
#
# TODO (production / Issue 7 — conversation history):
#   SESSION_STORE only tracks current slot state, not the full message
#   log.  For analytics, AI memory, and audit trails, persist each
#   (thread_id, role, content, timestamp) turn to a conversations table.

# Global in-memory conversation/session storage — DEV ONLY
SESSION_STORE: Dict[str, Dict[str, Any]] = {}

# Session TTL in seconds — inactive sessions older than this are pruned.
# 4 hours is generous enough for a single appointment booking flow.
SESSION_TTL_SECONDS: int = 4 * 60 * 60  # 4 hours


def touch_session(thread_id: str) -> None:
    """Update the last-active timestamp for a session."""
    if thread_id in SESSION_STORE:
        SESSION_STORE[thread_id]["_last_active"] = time.monotonic()


def purge_expired_sessions() -> int:
    """
    Remove sessions that have been inactive for longer than SESSION_TTL_SECONDS.

    Returns the number of sessions removed.
    Called periodically by the lifespan cleanup task.

    TODO (production / Issue 2): replace with Redis TTL keys so expiry is
    automatic and works across multiple server instances.
    """
    now = time.monotonic()
    expired = [
        tid
        for tid, sess in SESSION_STORE.items()
        if now - sess.get("_last_active", 0) > SESSION_TTL_SECONDS
    ]
    for tid in expired:
        SESSION_STORE.pop(tid, None)
    return len(expired)