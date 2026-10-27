"""The Design record: everything needed to regenerate a Cutter, plus the last result."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from pic2cookie.core.export import DEFAULT_PRINTER
from pic2cookie.core.model import (
    CutterParams,
    Dimensions,
    Feature,
    FilamentEstimate,
    FilamentParams,
    Role,
    TraceParams,
)


def now() -> datetime:
    return datetime.now(UTC)


class Source(BaseModel):
    filename: str
    kind: Literal["svg", "raster"]
    key: str  # file name within the Design


class DesignResult(BaseModel):
    style: str
    outline: str  # the Silhouette as SVG path data in mm
    features: list[Feature]
    warnings: list[str]
    estimate: FilamentEstimate
    dimensions: Dimensions
    generated: datetime = Field(default_factory=now)


class Design(BaseModel):
    id: str
    name: str
    created: datetime = Field(default_factory=now)
    updated: datetime = Field(default_factory=now)
    source: Source
    cutter: CutterParams = CutterParams()
    trace: TraceParams = TraceParams()
    filament: FilamentParams = FilamentParams()
    printer: str = DEFAULT_PRINTER
    roles: dict[str, Role] = {}
    status: Literal["new", "ready", "failed"] = "new"
    error: str | None = None
    result: DesignResult | None = None


class DesignPatch(BaseModel):
    """Changes to a Design; omitted fields stay as they are."""

    name: str | None = None
    cutter: CutterParams | None = None
    trace: TraceParams | None = None
    filament: FilamentParams | None = None
    printer: str | None = None
    roles: dict[str, Role] | None = None
