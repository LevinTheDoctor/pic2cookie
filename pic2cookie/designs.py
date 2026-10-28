"""The Design record: everything needed to regenerate its Product, plus the last result."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from pic2cookie.core.export import DEFAULT_PRINTER
from pic2cookie.core.model import (
    CoasterParams,
    CutterParams,
    Dimensions,
    Feature,
    FilamentEstimate,
    FilamentParams,
    Message,
    PartEstimate,
    Product,
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
    product: Product = Product.CUTTER
    style: str
    outline: str  # the Silhouette (Cutter) or Plate (Coaster) as SVG path data in mm
    features: list[Feature]
    warnings: list[Message]
    estimate: FilamentEstimate  # all parts together
    parts: list[PartEstimate] = []
    dimensions: Dimensions
    pause_z: float | None = None  # where to pause the print for the Coin insert
    generated: datetime = Field(default_factory=now)

    @field_validator("warnings", mode="before")
    @classmethod
    def _texts(cls, value):  # records from before warnings had codes
        return [Message.of(w) if isinstance(w, str) else w for w in value]


class Design(BaseModel):
    id: str
    name: str
    created: datetime = Field(default_factory=now)
    updated: datetime = Field(default_factory=now)
    source: Source
    product: Product = Product.CUTTER
    cutter: CutterParams = CutterParams()
    coaster: CoasterParams = CoasterParams()
    trace: TraceParams = TraceParams()
    filament: FilamentParams = FilamentParams()
    printer: str = DEFAULT_PRINTER
    roles: dict[str, Role] = {}
    status: Literal["new", "ready", "failed"] = "new"
    error: Message | None = None
    result: DesignResult | None = None

    @field_validator("error", mode="before")
    @classmethod
    def _text(cls, value):
        return Message.of(value) if isinstance(value, str) else value


class DesignPatch(BaseModel):
    """Changes to a Design; omitted fields stay as they are."""

    name: str | None = None
    product: Product | None = None
    cutter: CutterParams | None = None
    coaster: CoasterParams | None = None
    trace: TraceParams | None = None
    filament: FilamentParams | None = None
    printer: str | None = None
    roles: dict[str, Role] | None = None
