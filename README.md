# ServiceFlow AI (Public-Route)

ServiceFlow AI is a comprehensive, inclusive citizen intake and intelligent case processing platform. It enables citizens to report service issues (such as burst pipes, potholes, power outages, and waste management concerns) via voice notes or text, translates and processes the request using advanced language models, and routes the generated cases to the appropriate municipal or public service departments.

This repository is split into two primary components:
1. **[backend/](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/backend)**: A high-performance Python FastAPI service responsible for database persistence, case classification, routing, and conversational AI services.
2. **[frontend/](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/frontend)**: An Angular 19 web application providing a modern backoffice dashboard for agents, dispatchers, field teams, and supervisors to view, assign, and audit cases.

---

## Key Features

- **Multi-Lingual Voice & Text Intake**: Accepts text and audio messages. Supports automatic translation and transcription from local languages (including English, Shona, Ndebele, and Zulu) using AI models.
- **AI-Powered Detail Extraction**: Automatically extracts the core issue description and location from conversational messages. It accumulates details across multiple messages if any details are missing.
- **Conversational Feedback**: Generates natural speech responses using Text-to-Speech (TTS) models to guide the user in their own language.
- **Automated Case Routing & Classification**: Uses rule-based keyword classification and urgency analysis to assign cases to their respective departments and priority queues.
- **Omnichannel Support**: Includes support for web-based submissions and WhatsApp text/voice channels via webhooks.
- **Role-Based Operational Dashboard**: Custom management views for Citizens, Intake Officers, Dispatchers, Field Teams, Supervisors, Managers, Administrators, and Auditors.

---

## Tech Stack

### Backend
- **Framework**: Python FastAPI
- **Database ORM**: SQLAlchemy with PostgreSQL support
- **AI Integrations**: Large Language Models (LLM) and Text-to-Speech (TTS) integrations
- **Environment**: Uvicorn server, Dockerized deployment, and `loguru` logging
- **Core Files**:
  - [backend/main.py](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/backend/main.py): Application entry point and router setup.
  - [backend/Config/database.py](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/backend/Config/database.py): Database engine and session configuration.
  - [backend/Service/voice_service.py](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/backend/Service/voice_service.py): Speech processing, translation, and detail extraction logic.
  - [backend/Controller/whatsapp_controller.py](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/backend/Controller/whatsapp_controller.py): Webhook endpoints for messaging integration.

### Frontend
- **Framework**: Angular 19 (boilerplate details at [frontend/README.md](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/frontend/README.md))
- **UI Components**: PrimeNG, PrimeFlex, PrimeIcons
- **State/Routing**: RxJS, Angular Router, and API proxy routing defined in [frontend/proxy.conf.json](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/frontend/proxy.conf.json)

---

## Directory Structure

```
Public-Route/
├── backend/                  # FastAPI Application
│   ├── Config/               # Database and Middleware Configuration
│   ├── Controller/           # API Endpoint Handlers (Auth, Cases, Districts, WhatsApp, etc.)
│   ├── Entity/               # SQLAlchemy Models representing DB tables
│   ├── Repository/           # Database Query / Data Access Layer
│   ├── Schema/               # Pydantic Schemas for validation
│   ├── Service/              # Core Business Logic (Voice, Classification, Routing, Case)
│   ├── Utils/                # Utilities (Security, Seeding, Enums, Permissions)
│   ├── pyproject.toml        # Backend package configuration
│   └── requirements.txt      # Python dependencies list
│
└── frontend/                 # Angular Web Application
    ├── src/
    │   ├── app/
    │   │   ├── components/   # Common components (layout, navigation)
    │   │   ├── views/        # Pages (login, cases, districts, submit portal)
    │   │   └── services/     # Angular HTTP services
    │   └── assets/           # Static images and icons
    └── package.json          # Frontend packages and scripts
```

---

## Local Development Setup

### Backend Setup

1. **Navigate to the Backend Directory**:
   ```bash
   cd backend
   ```

2. **Create and Activate a Virtual Environment**:
   - On Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Alternatively, you can build/install via pyproject.toml:*
   ```bash
   pip install -e .
   ```

4. **Environment Variables Configuration**:
   Create a [backend/.env](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/backend/.env) file from your environment configurations. The following parameters are used:
   - `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql+psycopg2://username:password@localhost:5432/dbname`).
   - `SECRET_KEY`: Security signature key for auth token generation.
   - `GEMINI_API_KEY`: API access key for active translation, voice transcription, detail extraction, and TTS models.
   - `AFRICAS_TALKING_KEY` & `AFRICAS_TALKING_USERNAME`: Configuration parameters for auxiliary communication APIs.

5. **Automatic Migrations & Seeding**:
   The backend database tables are built on startup using SQLAlchemy's `create_all`. Database seeds are also applied automatically for:
   - An administrator account.
   - Starter districts (e.g., Harare Central, Bulawayo Central).
   - Organisation units and queues corresponding to classifications (Water, Roads, Power, Waste, etc.).
   - Demo role-based test accounts.

6. **Start the API Server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8015 --reload
   ```
   The API documentation will be available at `http://localhost:8015/docs`.

### Frontend Setup

1. **Navigate to the Frontend Directory**:
   ```bash
   cd ../frontend
   ```

2. **Install Node Packages**:
   Ensure you have Node.js and npm installed, then run:
   ```bash
   npm ci
   ```

3. **Start the Development Server**:
   ```bash
   npm start
   ```
   The application will run at `http://localhost:4200/`. API requests sent to `/api` are automatically proxied to the backend server via the target specified in [frontend/proxy.conf.json](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/frontend/proxy.conf.json).

---

## Seed Test Accounts

The platform populates the following accounts on first startup for local testing and quality assurance:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Super Admin** | `super.admin@serviceflow.ai` | `Demo@Admin` |
| **Citizen** | `citizen@demo.serviceflow.ai` | `Demo@Citizen` |
| **Intake Officer** | `intake.officer@demo.serviceflow.ai` | `Demo@IntakeOfficer` |
| **Dispatcher** | `dispatcher@demo.serviceflow.ai` | `Demo@Dispatcher` |
| **Field Team** | `field.team@demo.serviceflow.ai` | `Demo@FieldTeam` |
| **Supervisor** | `supervisor@demo.serviceflow.ai` | `Demo@Supervisor` |
| **Analyst** | `analyst@demo.serviceflow.ai` | `Demo@Analyst` |
| **Manager** | `manager@demo.serviceflow.ai` | `Demo@Manager` |
| **Administrator** | `admin@demo.serviceflow.ai` | `Demo@Administrator` |
| **Auditor** | `auditor@demo.serviceflow.ai` | `Demo@Auditor` |

---

## Docker Deployment

Both the frontend and backend are configured for containerized deployment.

### Build and Run Backend
From the root directory:
```bash
docker build -t serviceflow-backend -f backend/Dockerfile backend
docker run -d -p 8000:8000 --env-file backend/.env serviceflow-backend
```

### Build and Run Frontend
From the root directory:
```bash
docker build -t serviceflow-frontend -f frontend/Dockerfile frontend
docker run -d -p 3015:3015 serviceflow-frontend
```

---

## Messaging Channel Integration

The backend supports webhook triggers for messaging applications via [backend/Controller/whatsapp_controller.py](file:///d:/D_Documents/Dataal Africa/Ops Code/AI4Impact/Public-Route/backend/Controller/whatsapp_controller.py). 

To configure a webhook messaging gateway:
1. Expose your local backend server using a tunneling software (e.g. ngrok) to obtain a public HTTPS URL.
2. Register the webhook address on your gateway portal (e.g. Twilio sandbox dashboard):
   `https://<your-public-url>/api/v1/whatsapp/webhook`
3. Send a text or voice note to the configured sandbox number. The system will handle audio files (downloading and converting), extract key details, reply dynamically in the user's language, and automatically log the case to the admin dashboard when both the description and location are resolved.
