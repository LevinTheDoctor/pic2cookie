"""Design operations shared by the API, the CLI and the worker."""

import io
import logging
import uuid
from datetime import timedelta
from functools import cache
from pathlib import PurePath

lazy from PIL import Image, UnidentifiedImageError

from pic2cookie.core.export import Format, export, printer
from pic2cookie.core.model import Role
from pic2cookie.core.pipeline import make, to_svg
from pic2cookie.core.roles import path_data
from pic2cookie.core.trace import is_svg
from pic2cookie.designs import Design, DesignPatch, DesignResult, Source, now
from pic2cookie.settings import Settings, settings
from pic2cookie.storage import BlobStore, DesignRepo, NotFound, blob_store, design_repo

log = logging.getLogger(__name__)

PICTURE = "picture.svg"
ROLES = "roles.svg"
MEDIA_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".stl": "model/stl",
    ".3mf": "model/3mf",
}


class InvalidUpload(ValueError):
    pass


def media_type(name: str) -> str:
    return MEDIA_TYPES.get(PurePath(name).suffix.lower(), "application/octet-stream")


class DesignService:
    def __init__(self, blobs: BlobStore, repo: DesignRepo, cfg: Settings):
        self.blobs = blobs
        self.repo = repo
        self.cfg = cfg

    def _key(self, design_id: str, name: str) -> str:
        return f"designs/{design_id}/{name}"

    def create(self, filename: str, data: bytes, name: str | None = None) -> Design:
        limit = self.cfg.limits.upload_mb * 1024 * 1024
        if len(data) > limit:
            raise InvalidUpload(f"The file is larger than {self.cfg.limits.upload_mb:g} MB")
        if is_svg(data):
            kind, ext = "svg", ".svg"
        else:
            try:
                image = Image.open(io.BytesIO(data))
                fmt = image.format
            except (UnidentifiedImageError, OSError) as e:
                raise InvalidUpload("Upload an SVG, PNG, JPG or WebP picture") from e
            if fmt not in ("PNG", "JPEG", "WEBP"):
                raise InvalidUpload("Upload an SVG, PNG, JPG or WebP picture")
            if max(image.size) > self.cfg.limits.max_pixels:
                raise InvalidUpload(f"The picture is larger than {self.cfg.limits.max_pixels} px")
            kind, ext = "raster", {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[fmt]
        design_id = uuid.uuid4().hex[:12]
        stem = PurePath(filename).stem or "cutter"
        design = Design(
            id=design_id, name=name or stem, source=Source(filename=filename, kind=kind, key=f"source{ext}")
        )
        self.blobs.put(self._key(design_id, design.source.key), data, media_type(ext))
        self.repo.save(design)
        return design

    def get(self, design_id: str) -> Design:
        return self.repo.get(design_id)

    def list(self) -> list[Design]:
        return self.repo.list()

    def update(self, design_id: str, patch: DesignPatch) -> Design:
        design = self.get(design_id)
        changes = {k: getattr(patch, k) for k in patch.model_fields_set if getattr(patch, k) is not None}
        if "printer" in changes:
            printer(changes["printer"])  # raises for unknown printers
        if "trace" in changes and changes["trace"] != design.trace:
            changes.setdefault("roles", {})  # feature ids change with the tracing
        design = design.model_copy(update=changes | {"updated": now()})
        self.repo.save(design)
        return design

    def generate(self, design_id: str) -> Design:
        """Run the pipeline and store the picture, roles and Cutter files."""
        design = self.get(design_id)
        try:
            source = self.blobs.get(self._key(design_id, design.source.key))
            result = make(
                source,
                design.cutter,
                design.trace,
                design.filament,
                {k: Role(v) for k, v in design.roles.items()},
            )
            files = {
                PICTURE: result.svg.encode(),
                ROLES: result.marked_svg.encode(),
            }
            for fmt in Format:
                files[fmt.filename] = export(
                    result.cutter.mesh,
                    fmt,
                    name=design.name,
                    printer_id=design.printer,
                    material=design.filament.material,
                )
            for name, data in files.items():
                self.blobs.put(self._key(design_id, name), data, media_type(name))
        except Exception as e:  # noqa: BLE001 - any failure is reported on the Design
            log.exception("Generating design %s failed", design_id)
            design = self.get(design_id).model_copy(update={"status": "failed", "error": str(e)})
            self.repo.save(design)
            return design
        design = self.get(design_id).model_copy(
            update={
                "status": "ready",
                "error": None,
                "result": DesignResult(
                    style=result.layout.style,
                    outline=path_data(result.layout.silhouette),
                    features=[f.feature for f in result.layout.features],
                    warnings=result.cutter.warnings,
                    estimate=result.estimate,
                    dimensions=result.cutter.dimensions,
                ),
            }
        )
        self.repo.save(design)
        return design

    def picture(self, design_id: str) -> str:
        """The Design's picture as SVG, traced on demand."""
        design = self.get(design_id)
        if self.blobs.exists(self._key(design_id, PICTURE)):
            return self.blobs.get(self._key(design_id, PICTURE)).decode()
        return to_svg(self.blobs.get(self._key(design_id, design.source.key)), design.trace)

    def file(self, design_id: str, name: str) -> bytes:
        if "/" in name or name == "design.json":
            raise NotFound(name)
        self.get(design_id)
        return self.blobs.get(self._key(design_id, name))

    def files(self, design_id: str) -> list[str]:
        prefix = self._key(design_id, "")
        return [k[len(prefix) :] for k in self.blobs.list(prefix) if not k.endswith("design.json")]

    def duplicate(self, design_id: str) -> Design:
        design = self.get(design_id)
        copy = design.model_copy(
            update={
                "id": uuid.uuid4().hex[:12],
                "name": f"{design.name} (copy)",
                "created": now(),
                "updated": now(),
            }
        )
        for name in self.files(design_id):
            self.blobs.put(self._key(copy.id, name), self.file(design_id, name), media_type(name))
        self.repo.save(copy)
        return copy

    def delete(self, design_id: str) -> None:
        self.get(design_id)
        self.repo.delete(design_id)
        self.blobs.delete_prefix(f"designs/{design_id}/")

    def sweep(self) -> list[str]:
        """Delete Designs older than the retention period; returns their ids."""
        days = self.cfg.retention.days
        if not days:
            return []
        expired = self.repo.older_than(now() - timedelta(days=days))
        for design_id in expired:
            self.delete(design_id)
        return expired


@cache
def service() -> DesignService:
    cfg = settings()
    blobs = blob_store(cfg)
    return DesignService(blobs, design_repo(cfg, blobs), cfg)
