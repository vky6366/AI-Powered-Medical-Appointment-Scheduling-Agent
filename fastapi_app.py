from fastapi import FastAPI
from fastapi.responses import JSONResponse
import socket
app = FastAPI(title="RagaAI Scheduling Agent API")

@app.get("/stream")
async def stream():
    """Greeting endpoint for the scheduling agent."""
    greeting_message = {
        "message": "👋 Hello! I’m your AI scheduling assistant. How can I help you today?"
    }
    return JSONResponse(content=greeting_message)

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
    
    host_ip = "0.0.0.0"  # This allows external connections
    port = 5000
    
    print("\n" + "="*50)
    print(f"Server is running on:")
    print(f"Local URL:     http://localhost:{port}")
    print(f"Network URL:   http://{get_ip_address()}:{port}")
    print(f"API Docs URL:  http://{get_ip_address()}:{port}/docs")
    print("="*50 + "\n")
    
    # Run the server with these settings
    uvicorn.run(app, host=host_ip, port=port)