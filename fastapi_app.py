from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import socket
from agents.intake_agent import extract_patient_info
app = FastAPI(title="RagaAI Scheduling Agent API")

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from agents.intake_agent import extract_patient_info, PatientIntake

app = FastAPI(title="RagaAI Scheduling Agent API")

SESSION_STORE = {}

@app.get("/stream")
async def stream(
    q: str = Query(..., description="User input as free text"),
    thread_id: str = "default"
):
    # Get or initialize session state
    if thread_id not in SESSION_STORE:
        SESSION_STORE[thread_id] = PatientIntake()

    # Extract new info from this turn
    new_data: PatientIntake = extract_patient_info(q)

    # Merge new data into session
    session_data = SESSION_STORE[thread_id]
    for field, value in new_data.dict().items():
        if value not in [None, "", "null"]:  
            if field == "problem_description":
                # 🔹 Append instead of overwrite
                if session_data.problem_description:
                    session_data.problem_description += f". {value}"
                else:
                    session_data.problem_description = value
            else:
                setattr(session_data, field, value)

    # Conversation flow
    if not session_data.dob:
        next_question = "Got it 👍 Could you please tell me your date of birth (YYYY-MM-DD)?"
    elif not session_data.problem:
        next_question = "Thanks. Could you tell me briefly what issue you’re facing (e.g., allergies, fever, chest pain)?"
    elif not session_data.problem_description and session_data.description_turns < 2:
        session_data.description_turns += 1
        next_question = f"Got it. Could you describe your {session_data.problem} symptoms in more detail?"
    elif session_data.problem_description and session_data.description_turns < 2:
        session_data.description_turns += 1
        next_question = f"Thanks. Could you add one more detail about your {session_data.problem}?"
    elif not session_data.email:
        next_question = f"Thanks {session_data.name or 'there'}! Could you share your email so we can send confirmations?"
    elif not session_data.phone:
        next_question = "Perfect. And lastly, may I have your phone number for SMS reminders?"
    else:
        # Final summary message
        description_text = f"The patient is facing {session_data.problem_description}" if session_data.problem_description else session_data.problem
        next_question = (
            f"✅ All set, {session_data.name or 'patient'}! "
            f"I’ve noted: {description_text}. "
            f"Next, I’ll check available slots."
        )

    print("Session Data:", session_data)

    return JSONResponse(content={
        "message": next_question,
        "data": session_data.dict()
    })


def get_ip_address():
    try:
        # Get all network interfaces
        hostname = socket.gethostname()
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        # Filter out localhost and return the first valid IP
        return [ip for ip in ip_addresses if not ip.startswith("127.")][0]
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "0.0.0.0"

if __name__ == "__main__":
    import uvicorn
    
    host_ip = "0.0.0.0"  
    port = 5000
    
    print("\n" + "="*50)
    print(f"Server is running on:")
    print(f"Local URL:     http://localhost:{port}")
    print(f"Network URL:   http://{get_ip_address()}:{port}")
    print(f"API Docs URL:  http://{get_ip_address()}:{port}/docs")
    print("="*50 + "\n")
    
    uvicorn.run("fastapi_app:app", host=host_ip, port=port, reload=True)  