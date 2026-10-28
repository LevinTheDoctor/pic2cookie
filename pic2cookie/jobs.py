"""Generation jobs, run in a local thread pool (`inline`) or by RQ workers (`rq`)."""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from threading import Lock
from typing import Literal, Protocol

from pydantic import BaseModel
lazy import redis
lazy import rq
lazy from rq.exceptions import NoSuchJobError

from pic2cookie.settings import Settings, settings

log = logging.getLogger(__name__)

Status = Literal["queued", "running", "done", "failed"]


class Job(BaseModel):
    id: str
    design_id: str
    status: Status
    error: str | None = None


class Executor(Protocol):
    def submit(self, design_id: str) -> Job: ...
    def get(self, job_id: str) -> Job | None: ...


def run_generate(design_id: str) -> str:
    """The job itself; also the function RQ workers import."""
    from pic2cookie.service import service

    design = service().generate(design_id)
    if design.status == "failed":
        raise RuntimeError(design.error.text if design.error else "Generation failed")
    return design.id


class InlineExecutor:
    def __init__(self, workers: int = 2):
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="pic2cookie-job")
        self.jobs: dict[str, Job] = {}
        self.lock = Lock()

    def _set(self, job_id: str, **changes) -> None:
        with self.lock:
            self.jobs[job_id] = self.jobs[job_id].model_copy(update=changes)

    def _run(self, job_id: str, design_id: str) -> None:
        self._set(job_id, status="running")
        try:
            run_generate(design_id)
        except Exception as e:  # noqa: BLE001 - reported through the job
            self._set(job_id, status="failed", error=str(e))
        else:
            self._set(job_id, status="done")

    def submit(self, design_id: str) -> Job:
        job = Job(id=uuid.uuid4().hex, design_id=design_id, status="queued")
        with self.lock:
            if len(self.jobs) > 1000:  # forget old jobs
                for key in list(self.jobs)[:500]:
                    del self.jobs[key]
            self.jobs[job.id] = job
        self.pool.submit(self._run, job.id, design_id)
        return job

    def get(self, job_id: str) -> Job | None:
        with self.lock:
            return self.jobs.get(job_id)


class RqExecutor:
    QUEUE = "pic2cookie"

    def __init__(self, cfg: Settings):
        self.redis = redis.Redis.from_url(cfg.redis_url)
        self.queue = rq.Queue(self.QUEUE, connection=self.redis)
        self.timeout = cfg.limits.job_timeout

    def submit(self, design_id: str) -> Job:
        job = self.queue.enqueue(
            run_generate, design_id, job_timeout=self.timeout, result_ttl=3600, failure_ttl=86400
        )
        log.debug("Job queued", extra={"job_id": job.id, "design_id": design_id})
        return Job(id=job.id, design_id=design_id, status="queued")

    def get(self, job_id: str) -> Job | None:
        try:
            job = rq.job.Job.fetch(job_id, connection=self.redis)
        except NoSuchJobError:
            return None
        state = job.get_status(refresh=True)
        status: Status = {"finished": "done", "failed": "failed", "started": "running"}.get(state, "queued")
        error = None
        if status == "failed" and job.latest_result() is not None:
            error = (job.latest_result().exc_string or "").strip().splitlines()[-1:] or None
            error = error[0] if error else "Generation failed"
        return Job(id=job.id, design_id=job.args[0], status=status, error=error)


@cache
def executor() -> Executor:
    cfg = settings()
    return RqExecutor(cfg) if cfg.executor == "rq" else InlineExecutor()


def work(burst: bool = False) -> None:
    """Run an RQ worker for generation jobs."""
    ex = RqExecutor(settings())
    rq.Worker([ex.queue], connection=ex.redis).work(burst=burst)
