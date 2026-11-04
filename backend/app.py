import base64
import os
import secrets
import re
import json
import asyncio

from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, StreamingResponse

from pydantic import BaseModel, Field

from jobs import (
    InMemoryJobStore,
    JobManager,
    TERMINAL
)
import time
from collections import defaultdict, deque
from jobs import QueueFull 

from export import build_pdf

RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_HOUR", "5"))
_hits: dict[str, deque] = defaultdict(deque)


def check_rate_limit(request: Request):
    fwd = request.headers.get("x-forwarded-for")
    ip = fwd.split(",")[-1].strip() if fwd else (request.client.host if request.client else "unknown")
    now, q = time.time(), _hits[ip]
    while q and q[0] < now - 3600:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise HTTPException(429, "Research limit reached. Please try again in an hour.",
                            headers={"Retry-After": "3600"})
    q.append(now)

app = FastAPI(title="MindMesh API")


@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    password = os.getenv("APP_PASSWORD")

    if not password or request.url.path == "/api/health":
        return await call_next(request)

    header = request.headers.get("authorization", "")

    if header.startswith("Basic "):
        try:
            decoded = base64.b64decode(header[6:]).decode()
            user, _, pw = decoded.partition(":")

            if (
                secrets.compare_digest(user, os.getenv("APP_USER", "mindmesh"))
                and secrets.compare_digest(pw, password)
            ):
                return await call_next(request)

        except Exception:
            pass

    return Response(
        content='{"detail":"Authentication required"}',
        status_code=401,
        media_type="application/json",
        headers={"WWW-Authenticate": 'Basic realm="MindMesh"'}
    )

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])
store = InMemoryJobStore()          # swap for a SQLite-backed JobStore later
manager = JobManager(store)


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)


def _job_or_404(job_id: str) -> dict:
    job = store.snapshot(job_id)
    if job is None:
        raise HTTPException(404, "This research job no longer exists. The server may have restarted.")
    return job


def _completed(job_id: str) -> dict:
    job = _job_or_404(job_id)
    if job["status"] != "completed":
        raise HTTPException(409, f"Report is not ready (job is {job['status']}).")
    return job


def _slug(topic: str) -> str:
    return re.sub(r"\W+", "-", topic.lower()).strip("-")[:40] or "report"


@app.post("/api/research", status_code=202)
async def start_research(req: ResearchRequest, request: Request):
    check_rate_limit(request)
    try:
        return {"job_id": manager.submit(req.topic.strip())}
    except QueueFull:
        raise HTTPException(503, "The research queue is full. Please try again in a few minutes.")


@app.get("/api/research/{job_id}")
async def get_research(job_id: str):
    return _job_or_404(job_id)


@app.get("/api/research/{job_id}/events")
async def research_events(job_id: str, request: Request, after: int = 0):
    """SSE. Every event has an id, so a browser reconnect (Last-Event-ID) or a fresh
    page load (?after=) resumes exactly where it left off. Finished jobs replay and close."""
    _job_or_404(job_id)
    last = request.headers.get("last-event-id", "")
    cursor = int(last) if last.isdigit() else after

    async def stream():
        cur, idle = cursor, 0.0
        yield "retry: 2000\n\n"
        while not await request.is_disconnected():
            events = store.events_after(job_id, cur)
            if events is None:
                return
            for ev in events:
                cur = ev["seq"]
                yield f"id: {cur}\ndata: {json.dumps(ev)}\n\n"
                if ev["type"] == "job" and ev["status"] in TERMINAL:
                    return
            idle = 0.0 if events else idle + 0.5
            if idle >= 15:
                yield ": keep-alive\n\n"; idle = 0.0
            await asyncio.sleep(0.5)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/research/{job_id}/report.md")
async def report_md(job_id: str):
    job = _completed(job_id)
    return Response(job["result"]["report"], media_type="text/markdown; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="mindmesh-{_slug(job["topic"])}.md"'})


@app.get("/api/research/{job_id}/report.pdf")
def report_pdf(job_id: str):
    job = _completed(job_id)
    pdf = build_pdf(job["topic"], job["result"]["report"], job["created_at"])
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="mindmesh-{_slug(job["topic"])}.pdf"'})


@app.get("/api/health")
async def health():
    return {"ok": True}


FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():  # present in Docker; absent during local dev
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")