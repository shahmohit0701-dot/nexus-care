# NEXUS CARE — Smart Clinical Triage System

A capstone-ready multimodal clinical-triage prototype inspired by the approved project proposal. It combines conversational intake, symptom NLP, disease/symptom ML, ESI-style urgency scoring, FHIR-style records, hospital queue management, emergency workflows, browser camera monitoring, geolocation, role-based dashboards, and explainable AI output.

> **Safety / academic prototype:** This system is for demonstration and research only. It is not a medical diagnostic device, does not replace a clinician, and its emergency workflow is simulated. Never rely on it for real medical decisions.

## Stack
- Frontend: React 18 (CDN runtime for zero-build demo), Tailwind CSS CDN, Web APIs
- Backend: Python FastAPI + WebSockets
- ML: XGBoost + scikit-learn, Pandas, NumPy
- Data: disease/symptom seed data + generated synthetic training records
- EHR: FHIR-style JSON export / parsing
- Persistence: SQLite demo database by default; PostgreSQL Docker configuration included
- NLP: lightweight clinical entity/negation/severity/duration extraction implemented in Python, with extension points for medspaCy/scispaCy

## Quick start — easiest
Windows:
1. Install Python 3.11+.
2. Open this folder in VS Code.
3. Run `start_demo.bat`.
4. Open http://127.0.0.1:8000

Or:
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/train_model.py
uvicorn backend.app:app --reload --port 8000
```

## Demo accounts
- Patient: `patient@demo.com` / `demo123`
- Clinician: `doctor@demo.com` / `demo123`
- Admin: `admin@demo.com` / `demo123`

The login is intentionally a local demo credential system. Replace with proper OAuth/identity infrastructure for any real deployment.

## Features
### Patient
- First-time medical profile onboarding
- Medical history, allergies, medications, emergency contact
- AI conversational triage intake
- Symptom entity extraction, negation, duration and severity parsing
- Possible-condition ML ranking using XGBoost
- ESI-style urgency score with explainability
- Emergency button
- Browser camera / Guardian Vision monitoring
- Browser geolocation during emergency flow
- Ambulance dispatch simulation
- Patient timeline and FHIR-style record

### Hospital / clinician
- Live WebSocket queue
- ESI priority ordering
- Red-alert emergency cards
- Patient medical history
- AI triage summary
- Risk contributors and confidence
- Approve / override triage
- Ambulance status
- FHIR export

### Admin
- System KPIs
- Disease model metrics
- Hospital and user counts
- Emergency analytics
- Recent audit events
- Dataset/model information

## ML dataset
`data/disease_symptom_profiles.csv` contains curated symptom profiles for 20 common conditions used **only as a synthetic educational seed**. `backend/train_model.py` expands these profiles into noisy synthetic patient examples and trains an XGBoost multiclass classifier. The app reports ranked possible conditions rather than a diagnosis.

To retrain:
```bash
python backend/train_model.py
```

Model artifact: `data/triage_model.joblib`.

## PostgreSQL
A production-style PostgreSQL configuration is included in `docker-compose.yml`. The demo defaults to SQLite so the project can be launched without Docker. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL and adapt the repository layer before production deployment.

## Camera / Guardian Vision
The browser asks for camera permission only when Guardian Vision is enabled. The current prototype performs client-side frame-difference / motion analysis and posture-event simulation hooks; it intentionally does **not** claim to diagnose cardiac arrest, stroke, or disease from a camera. For the capstone, this is a working multimodal emergency-event prototype and can later be upgraded to MediaPipe/OpenCV pose estimation.

## Important
The system intentionally uses a human-in-the-loop model: the AI proposes urgency; a clinician can approve or override it. The emergency button and ambulance workflow are simulated for the college project.

## Proposal technology mapping
- Node.js + Express.js: `gateway/` architectural gateway
- Python + FastAPI: `backend/` working clinical/ML API
- React + Tailwind: `frontend/` zero-build demo client
- XGBoost + scikit-learn: trained model in `data/triage_model.joblib`
- NumPy/Pandas/JSON: model/data processing
- medspaCy/scispaCy: optional adapters in `backend/clinical_nlp.py` and `backend/requirements-optional-nlp.txt`
- PostgreSQL: `docker-compose.yml` configuration; SQLite is the no-setup demo persistence layer


## Blank page fix (v1.1)
The frontend is intentionally dependency-free in the browser. It no longer requires React/Babel/Tailwind CDN access, so it works when the machine has no internet connection. The UI is rendered with vanilla JavaScript and local CSS while retaining the React/Tailwind-inspired design language. The emergency database insert and WebSocket protocol were also corrected.

### Demo credentials
- Patient: `patient@demo.com` / `demo123`
- Clinician: `doctor@demo.com` / `demo123`
- Admin: `admin@demo.com` / `demo123`

## If port 8000 shows `[object Promise]`
That means an older local server is answering on port 8000. Use `start_demo_8010.bat` for a clean launch at `http://127.0.0.1:8010`.

## Guardian Vision note
Guardian Vision auto-starts for the patient workspace. Web browsers intentionally control camera access and may display their own camera permission prompt; a website cannot silently bypass that security boundary. NEXUS CARE does not show a second in-app permission dialog. Video is processed locally in the browser for the prototype motion check and is not uploaded or stored.

## V7 upgrade
Use `start_demo_8050.bat` for the cinematic launch experience. V7 adds a multi-stage animated startup, Care Copilot handoff export, Health Twin readiness visualization, and additional UI motion polish.
