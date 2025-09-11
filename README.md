# AI-Powered Medical Appointment Scheduling Agent

An intelligent, AI-powered agent designed to automate and optimize the scheduling of medical appointments. This project aims to streamline patient-doctor interactions, reduce manual administrative work, and improve the overall efficiency of medical appointment management.

## Features

- **AI-Powered Scheduling**: Automatically suggests optimal appointment slots based on doctor availability, patient preferences, and clinic constraints.
- **Natural Language Processing**: Understands and responds to patient queries using conversational AI.
- **Calendar Integration**: Syncs appointments with major calendar providers.
- **Multi-User Support**: Handles scheduling for multiple doctors and patients.
- **Reminders and Notifications**: Sends automated reminders and updates via email or SMS.
- **Customizable Rules**: Easily configure scheduling rules and policies.

## Technologies Used

- Python (Core logic and backend)
- FastAPI (Backend API server)
- Streamlit (Frontend UI)
- Machine Learning / NLP models
- Integration APIs: Calendar, SMS, Email

## Installation

1. **Clone the Repository**
    ```bash
    git clone https://github.com/vky6366/AI-Powered-Medical-Appointment-Scheduling-Agent.git
    cd AI-Powered-Medical-Appointment-Scheduling-Agent
    ```

2. **Setup Python Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Configure Environment Variables**
    - In `.env` and fill in your API keys, database URLs, etc.

## Run Application

Open **two terminals**:

**Terminal 1:** Start the FastAPI backend
```bash
python fastapi_app.py
```

**Terminal 2:** Start the Streamlit frontend
```bash
streamlit run streamlit_app.py
```

## Usage

- Access the web UI via Streamlit and interact with the scheduling agent.
- The backend API (FastAPI) powers the logic and data processing.
- Refer to the API documentation for custom integrations.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature`.
3. Commit your changes and push to your branch.
4. Open a pull request describing your changes.

## License

This project is licensed under the MIT License.

## Contact

For questions, feature requests, or support, open an issue or contact [@vky6366](https://github.com/vky6366).
