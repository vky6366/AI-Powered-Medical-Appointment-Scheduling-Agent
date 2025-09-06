from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents import intake_graph, PatientIntake
from api import get_routers
from api.utils import patient_to_dict, dict_to_patient, get_ip_address
from api.config import APP_TITLE

app = FastAPI(title=APP_TITLE)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conversation state (simple in-memory)
SESSION_STORE: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
async def health():
    return {"ok": True, "app": APP_TITLE}


@app.get("/stream")
async def stream(
    q: str = Query(...),
    thread_id: str = Query("default"),
):
    session = SESSION_STORE.setdefault(thread_id, {
        "patient": PatientIntake(),
        "next_step": None,
        "booking_done": False,   # <-- add default
    })
    patient: PatientIntake = session["patient"]

    state = {
        "input_text": q,
        "patient": patient,
        "next_step": session.get("next_step"),
        "booking_done": session.get("booking_done", False),   # <-- pass in
    }

    try:
        result = intake_graph.invoke(state)
        # DEBUG
        try:
            dbg = result.get("patient") or session.get("patient")
            print("\n=== DEBUG: PatientIntake state ===")
            print((dbg.model_dump() if hasattr(dbg, "model_dump") else dict(dbg)))
            print("==================================\n")
        except Exception:
            pass
    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"agent_error: {e.__class__.__name__}: {e}"})

    # persist updates
    new_patient = result.get("patient")
    if new_patient is not None:
        try:
            session["patient"] = new_patient if isinstance(new_patient, PatientIntake) else dict_to_patient(new_patient)
        except Exception:
            pass

    session["next_step"] = result.get("next_step")  # persist the question
    # booking_done may be updated by other endpoints; we leave it intact here

    message = result.get("message") or result.get("reply") or "Okay."
    return {"message": message, "data": patient_to_dict(session.get("patient")), "next_step": session["next_step"]}





# Mount all other routers from api/
for router in get_routers():
    app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    host_ip = "0.0.0.0"
    port = int(os.getenv("PORT", "5000"))

    print("\n" + "=" * 50)
    print(f"Server is running on:")
    print(f"Local URL:     http://localhost:{port}")
    print(f"Network URL:   http://{get_ip_address()}:{port}")
    print(f"API Docs URL:  http://{get_ip_address()}:{port}/docs")
    print("=" * 50 + "\n")

    uvicorn.run("fastapi_app:app", host=host_ip, port=port, reload=True)
