# Mindful Companion

An AI-powered mental health MVP with:
- Chat companion (OpenAI or local fallback)
- Mood tracking (trend chart) and journaling
- Crisis and support resources

This is an educational tool, not medical advice. If you are in crisis, call your local emergency number or a crisis hotline immediately.

## Tech
- Backend: FastAPI + SQLModel (SQLite)
- Frontend: Static HTML/CSS/JS + Chart.js

## Setup
1. Install Python 3.10+
2. Create a virtual environment and install deps:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
3. Optional: set environment variables for AI chat
```
set OPENAI_API_KEY=your_key
set OPENAI_MODEL=gpt-4o-mini
```
4. Run the server:
```
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
5. Open the app at `http://localhost:8000`

## API
- POST `/api/chat`
- CRUD `/api/moods/`
- CRUD `/api/journal/`
- GET `/api/resources/`

## Safety
- The AI avoids diagnoses and provides supportive, brief guidance
- Crisis resources are included in-app
- Do not rely on this for emergencies or clinical use


