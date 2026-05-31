# 🩺 AI-Powered Medical Appointment Scheduling Agent

An advanced, production-grade conversational healthcare intake and appointment scheduling ecosystem. 

Powered by **LangGraph** (state machine orchestrations), **FastAPI** (asynchronous backend router), and a modern **React 19 SPA** (Vite + Tailwind CSS), this project automates the patient intake pipeline. It intelligently extracts symptoms, validates demographics and insurance carriers, maps clinical issues to provider specialties, suggests available slots, handles secure scheduling, and dispatches automated PDF booking receipts via email notifications.

---

## 🌟 Key Features

*   **Stateful AI Intake Agent:** Built on **LangGraph** and **LangChain** to orchestrate step-by-step intake sessions. Avoids conversational regressions and duplicate queries using custom inline regex and LLM extraction pipelines (`o4-mini-2025-04-16` / `gpt-4o-mini`).
*   **Provider Recommendations:** Evaluates natural symptoms (e.g., matching a cold to a general practitioner or tooth pain to a dentist) and suggests suitable specialists automatically.
*   **Dual Frontend Clients:**
    *   **React 19 Web App:** Built with Tailwind CSS, Axios, and Firebase Authentication, offering a clean patient dashboard, conversational chat widget, profile manager, and booking calendar.
    *   **Streamlit Console:** A diagnostic companion playground for developers to test session variables, JWT authentications, and LangGraph turn-by-turn state machines.
*   **Production API Backend:** FastAPI endpoints supporting stateful TTL session cleanup, JWT-based security middleware via Google OAuth, and asynchronous task processing.
*   **Robust Reporting & Notifications:**
    *   Generates elegant PDF booking cards dynamically using ReportLab.
    *   Dispatches SMTP email notifications (supporting both TLS and SSL configurations) with local outbox `.eml` spooling as a network failure fallback.
    *   Automates pre-visit intake forms distribution.
*   **Scheduled Reminders:** Generates operational reminder queues set to notify patients 30 minutes prior to scheduled visits.

---

## 🏗️ Architectural Blueprint

The workflow follows a state-machine path:

```
                  ┌──────────────────────┐
                  │      START Node      │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐  Yes  ┌──────────────────────┐
                  │ Is next_step Slot?  ─┼─────►│ Book Appointment /   │
                  └──────────┬───────────┘       │ Await Slot Selection │
                             │ No                └──────────────────────┘
                  ┌──────────▼───────────┐
                  │ NLP Extraction Node  │
                  └──────────┬───────────┘
                             │
                             ▼
         Iteratively evaluates missing fields:
  ┌──────────────────┬──────────────────┬──────────────────┐
  ▼                  ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Ensure Symptoms │ │ Ensure Returning │ │  Ensure Doctor   │ │   Ensure Date    │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │                    │
         └────────────────────┼────────────────────┴────────────────────┘
                              │ All fields present
                     ┌────────▼─────────┐
                     │   Fetch Slots    │
                     └──────────────────┘
```

---

## 📁 Repository Structure

```
AI-Powered-Medical-Appointment-Scheduling-Agent/
├── fastapi_app.py           # FastAPI server entry point (session logs, rate limiting, and CORS)
├── streamlit_app.py         # Streamlit companion chat dashboard for backend testing
├── Dockerfile               # Production multi-stage Docker build recipe
├── docker-compose.yml       # Launches databases, APIs, and frontends containerized
├── requirements.txt         # Backend Python packages (LangGraph, FastAPI, reportlab, SQLAlchemy)
│
├── agents/                  # AI Intake Agent & Core Database Definitions
│   ├── extract.py           # Structured parameter extraction chains (using ChatOpenAI)
│   ├── flow.py              # LangGraph conditional edge and state-machine compile definitions
│   ├── nodes.py             # Chatbot graph nodes (Problem, Returning, Doctor, Slots, Booking)
│   ├── models.py            # SQLAlchemy PostgreSQL database schemas (Users, Doctors, Bookings)
│   └── db_service.py        # Relational SQL CRUD methods (seeding, bookings, cancellations)
│
├── api/                     # FastAPI Routing & Core Services
│   ├── auth_router.py       # Google OAuth SSO integrations & JWT authentication
│   ├── routes/
│   │   ├── scheduling.py    # Calendar scheduling, cancellations, and spreadsheets backups
│   │   └── ops.py           # Admin outbox logs, test email triggers, and scheduled reminders
│   └── services/
│       ├── notify.py        # Dual-port SMTP mail engine (TLS/SSL, fallback outbox .eml builder)
│       └── calendar.py      # Automated calendar grid tools
│
└── frontend/                # React 19 Single Page Web App (Vite + Tailwind CSS)
    ├── src/
    │   ├── components/      # Workspaces (ChatTab, AppointmentsTab, ScheduleTab, ProfileTab)
    │   ├── context/         # AuthContext verified via Firebase Admin and Google OAuth
    │   └── pages/           # Landing, demographic updates, and main Dashboard pages
```

---

## 🚀 Getting Started

### 📋 Prerequisites

*   Python 3.10+
*   Node.js 18+
*   PostgreSQL
*   OpenAI API Key

### 🛠️ Environment Variables Setup

Create a `.env` file in the root directory:

```env
# Database Credentials
DATABASE_URL=postgresql://user:password@localhost:5432/medical_db

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Authentication (Firebase & Google OAuth)
FIREBASE_SERVICE_ACCOUNT_JSON=path-to-firebase-credentials.json

# SMTP Configuration (TLS / SSL Mailers)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM=no-reply@clinic.com
SMTP_USE_TLS=true
```

---

## 💻 Running the Application

### 🐳 Method A: Containerized Deployment (Recommended)

To spin up the entire ecosystem (PostgreSQL database, FastAPI backend, and React frontend) in a single command:

```bash
docker-compose up --build
```

---

### 🐍 Method B: Local Manual Setup

#### 1. Setup Backend API Server
Navigate to the root directory, create a virtual environment, install requirements, and run the FastAPI server:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database
python -c "from agents.seed_data import seed_db; seed_db()"

# Launch the backend server
python fastapi_app.py
```
The FastAPI application will start on `http://localhost:5000`. You can access automated Swagger documentation at `http://localhost:5000/docs`.

#### 2. Run Streamlit Dashboard Client
In a separate terminal window with your virtual environment active, run the diagnostic dashboard:

```bash
streamlit run streamlit_app.py
```

#### 3. Run React Frontend Web App
Navigate to the frontend directory, install npm packages, and launch the Vite development server:

```bash
cd frontend
npm install
npm run dev
```
The React single page application will open locally at `http://localhost:5173`.

---

## 🧪 Running Tests & Diagnostics

To quickly check the integrity of your database connection and operational availability routines:

```bash
# Run backend database diagnostics
python agents/db_test.py
```

---

## 🔒 Security & Privacy

*   **Zero Symptom URL Exposure:** All medical queries, symptoms, and DOB data are transmitted exclusively within encrypted POST request bodies. No health parameters are passed through URL parameters or written to server console logs.
*   **Authentication Guards:** Custom React Route-guards filter unauthorized users and enforce complete clinical/demographic profiles before allowing booking operations.
*   **JWT Integrity checks:** Every scheduling request verifies security signatures using JWT payloads via Google OAuth and Firebase integration.
