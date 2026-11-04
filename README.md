# MindMesh

```
backend/   agents.py tools.py (yours) · pipeline.py · jobs.py · export.py · app.py
frontend/  React + Vite
```
1. Copy your `agents.py`, `tools.py`, `.env` (GROQ_API_KEY, TAVILY_API_KEY) into `backend/`.
2. `cd backend && pip install -r requirements.txt && uvicorn app:app --reload --port 8000`
3. `cd frontend && npm install && npm run dev` → http://localhost:5173

A running or finished job is addressable at `/?job=<id>`; reloading the page resumes it.
`python pipeline.py` still works in the terminal. To persist jobs, implement `JobStore` (see `jobs.py`) on SQLite and pass it to `JobManager` in `app.py`.
