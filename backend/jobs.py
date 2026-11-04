"""Job management. `JobStore` is the seam: swap InMemoryJobStore for a SQLite
implementation of the same methods without touching app.py or JobManager."""
import copy, threading, time, uuid
from typing import Optional, Protocol
from pipeline import STAGES, run_research_pipeline

TERMINAL = ("completed", "failed")


class JobStore(Protocol):
    def create(self, topic: str) -> str: ...
    def snapshot(self, job_id: str) -> Optional[dict]: ...
    def events_after(self, job_id: str, seq: int) -> Optional[list]: ...
    def set_running(self, job_id: str) -> None: ...
    def record_stage(self, job_id: str, stage: str, status: str, error: Optional[str] = None) -> None: ...
    def finish(self, job_id: str, result: Optional[dict] = None, error: Optional[str] = None) -> None: ...
    def prune(self, max_age_s: float) -> None: ...


class InMemoryJobStore:
    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _event(self, job, **fields):
        job["events"].append({"seq": len(job["events"]) + 1, "ts": time.time(), **fields})

    def create(self, topic):
        job_id = uuid.uuid4().hex
        job = {"id": job_id, "topic": topic, "status": "queued", "error": None, "result": None,
               "created_at": time.time(), "finished_at": None, "events": [],
               "stages": {s: {"status": "waiting", "error": None, "started_at": None, "finished_at": None}
                          for s in STAGES}}
        with self._lock:
            self._jobs[job_id] = job
            self._event(job, type="job", status="queued")
        return job_id

    def snapshot(self, job_id):
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return None
            snap = {k: v for k, v in j.items() if k != "events"}
            snap["stages"] = copy.deepcopy(j["stages"])
            snap["last_seq"] = len(j["events"])
            return snap

    def events_after(self, job_id, seq):
        with self._lock:
            j = self._jobs.get(job_id)
            return None if j is None else list(j["events"][seq:])

    def set_running(self, job_id):
        with self._lock:
            j = self._jobs[job_id]
            j["status"] = "running"
            self._event(j, type="job", status="running")

    def record_stage(self, job_id, stage, status, error=None):
        with self._lock:
            j = self._jobs[job_id]
            st = j["stages"][stage]
            st["status"], st["error"] = status, error
            if status == "running":
                st["started_at"] = time.time()
            else:
                st["finished_at"] = time.time()
            self._event(j, type="stage", stage=stage, status=status)

    def finish(self, job_id, result=None, error=None):
        with self._lock:
            j = self._jobs[job_id]
            j["status"] = "failed" if error else "completed"
            j["result"], j["error"], j["finished_at"] = result, error, time.time()
            self._event(j, type="job", status=j["status"])

    def prune(self, max_age_s):
        cutoff = time.time() - max_age_s
        with self._lock:
            for k in [k for k, j in self._jobs.items() if j["finished_at"] and j["finished_at"] < cutoff]:
                del self._jobs[k]


class JobManager:
    def __init__(self, store: JobStore, max_age_s: float = 3600, max_concurrent: int = 1):
        self.store, self.max_age_s = store, max_age_s
        self._slots = threading.BoundedSemaphore(max_concurrent)

    def submit(self, topic: str) -> str:
        self.store.prune(self.max_age_s)
        job_id = self.store.create(topic)
        threading.Thread(target=self._run, args=(job_id, topic), daemon=True,
                         name=f"research-{job_id[:8]}").start()
        return job_id

    def _run(self, job_id, topic):
        with self._slots:  # the job stays "queued" until a slot is free
            s = self.store
            s.set_running(job_id)

            def on_event(e):
                s.record_stage(job_id, e["stage"], e["status"], e["content"] if e["status"] == "failed" else None)

            try:
                s.finish(job_id, result=run_research_pipeline(topic, on_event=on_event))
            except Exception as e:
                s.finish(job_id, error=f"{type(e).__name__}: {e}")