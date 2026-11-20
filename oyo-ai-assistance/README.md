# Oyo AI Assistance

German phone voice assistant for your OYO hotel (set HOTEL_NAME in .env) (FastAPI + Vonage Voice + Groq).
Sessions are kept in plain Python dicts/lists (`app/store.py`) - no Redis needed.
Data is lost on restart; run with a single uvicorn worker.

## Run
```bash
cp .env.example .env        # set GROQ_API_KEY
pip install -r requirements.txt
python -m uvicorn server:app --port 8000
```
Open http://localhost:8000/health and http://localhost:8000/debug/calls
