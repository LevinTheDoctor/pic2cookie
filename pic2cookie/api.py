"""Web API (FastAPI). Also serves the built frontend, if there is one."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pic2cookie import __version__
from pic2cookie.core.export import DEFAULT_PRINTER, Format, printers
from pic2cookie.core.model import DENSITY, CutterParams, FilamentParams, TraceParams
from pic2cookie.designs import Design, DesignPatch
from pic2cookie.jobs import Job, executor
from pic2cookie.service import InvalidUpload, media_type, service
from pic2cookie.settings import settings
from pic2cookie.storage import NotFound

log = logging.getLogger(__name__)
FRONTEND = Path(__file__).parent.parent / "frontend" / "dist"


class DesignWithJob(BaseModel):
    design: Design
    job: Job | None = None


async def _sweep_forever() -> None:
    while True:
        try:
            removed = await asyncio.to_thread(service().sweep)
            if removed:
                log.info("Retention removed %d design(s)", len(removed))
        except Exception:
            log.exception("Retention sweep failed")
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sweep_forever()) if settings().retention.days else None
    yield
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Pic2Cookie", version=__version__, lifespan=lifespan)


def _design(design_id: str) -> Design:
    try:
        return service().get(design_id)
    except NotFound:
        raise HTTPException(404, "Design not found") from None


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/meta")
def meta() -> dict:
    cfg = settings()
    return {
        "version": __version__,
        "printers": [
            {"id": p.id, "name": p.name, "bed": p.bed, "height": p.height, "materials": list(p.materials)}
            for p in printers()
        ],
        "default_printer": DEFAULT_PRINTER,
        "materials": {m.value: {"density": d} for m, d in DENSITY.items()},
        "formats": [{"id": f.value, "filename": f.filename} for f in Format],
        "defaults": {
            "cutter": CutterParams().model_dump(),
            "trace": TraceParams().model_dump(),
            "filament": FilamentParams().model_dump(),
        },
        "limits": cfg.limits.model_dump(),
        "executor": cfg.executor,
    }


@app.get("/api/designs")
def list_designs() -> list[Design]:
    return service().list()


@app.post("/api/designs", status_code=201)
async def create_design(
    file: Annotated[UploadFile, File()], name: Annotated[str | None, Form()] = None
) -> DesignWithJob:
    data = await file.read()
    try:
        design = await asyncio.to_thread(service().create, file.filename or "picture", data, name)
    except InvalidUpload as e:
        raise HTTPException(422, str(e)) from None
    return DesignWithJob(design=design, job=executor().submit(design.id))


@app.get("/api/designs/{design_id}")
def get_design(design_id: str) -> Design:
    return _design(design_id)


@app.patch("/api/designs/{design_id}")
def update_design(design_id: str, patch: DesignPatch, generate: bool = True) -> DesignWithJob:
    _design(design_id)
    try:
        design = service().update(design_id, patch)
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    return DesignWithJob(design=design, job=executor().submit(design_id) if generate else None)


@app.post("/api/designs/{design_id}/generate", status_code=202)
def generate_design(design_id: str) -> Job:
    _design(design_id)
    return executor().submit(design_id)


@app.post("/api/designs/{design_id}/duplicate", status_code=201)
def duplicate_design(design_id: str) -> Design:
    _design(design_id)
    return service().duplicate(design_id)


@app.delete("/api/designs/{design_id}", status_code=204)
def delete_design(design_id: str) -> Response:
    _design(design_id)
    service().delete(design_id)
    return Response(status_code=204)


@app.get("/api/designs/{design_id}/files/{name}")
def design_file(design_id: str, name: str, download: bool = False) -> Response:
    design = _design(design_id)
    try:
        data = service().file(design_id, name)
    except NotFound:
        raise HTTPException(404, "File not found") from None
    headers = {"Cache-Control": "no-cache"}
    if download:
        filename = f"{design.name}{name.removeprefix('cutter')}" if name.startswith("cutter") else name
        headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return Response(data, media_type=media_type(name), headers=headers)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> Job:
    job = executor().get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job


def _mount_frontend() -> None:
    root = settings().frontend_dir or FRONTEND
    if not (root / "index.html").exists():
        return
    app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(404)
        file = (root / path).resolve()
        if path and file.is_file() and file.is_relative_to(root.resolve()):
            return FileResponse(file)
        return FileResponse(root / "index.html")


_mount_frontend()
