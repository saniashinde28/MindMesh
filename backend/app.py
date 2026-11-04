import asyncio, json, re
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from export import build_pdf
from jobs import TERMINAL, InMemoryJobStore, JobManager

app = FastAPI(title="MindMesh API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

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
async def start_research(req: ResearchRequest):
    return {"job_id": manager.submit(req.topic.strip())}


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
