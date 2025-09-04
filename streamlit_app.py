import streamlit as st
import requests

FASTAPI_URL = "http://192.168.187.101:5000"  # FastAPI backend

# Initialize session state for messages
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    # Add initial greeting only once
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': "👋 Hello! I’m your AI scheduling assistant. How can I help you today?"
    })

# Render conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Input box
user_input = st.chat_input('Type here...')

if user_input:
    # Save and display user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Call FastAPI backend
    try:
        response = requests.get(f"{FASTAPI_URL}/stream", params={"q": user_input})
        if response.status_code == 200:
            ai_message = response.json().get("message", "⚠️ No response from agent")
        else:
            ai_message = f"⚠️ Error {response.status_code}: Could not reach backend."
    except Exception as e:
        ai_message = f"⚠️ Backend error: {str(e)}"

    # Save and display assistant response
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
    with st.chat_message('assistant'):
        st.text(ai_message)
