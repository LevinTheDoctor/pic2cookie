"""Parameters and results shared by the core, the CLI and the API (lengths in mm)."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Role(StrEnum):
    OUTER = "outer"
    HOLE = "hole"
    IMPRINT = "imprint"
    IGNORE = "ignore"


class Material(StrEnum):
    PLA = "pla"
    PETG = "petg"
    ABS = "abs"


# g/cm³
DENSITY: dict[Material, float] = {Material.PLA: 1.24, Material.PETG: 1.27, Material.ABS: 1.04}


class CutterParams(BaseModel):
    size: float = Field(80.0, gt=5, le=400, description="Longest side of the Silhouette")
    blade_height: float = Field(15.0, gt=2, le=100)
    blade_thickness: float = Field(0.8, ge=0.4, le=5)
    flange_width: float = Field(4.0, ge=0, le=30)
    flange_height: float = Field(2.0, gt=0, le=10)
    imprint_offset: float = Field(3.0, ge=0.5, le=50, description="How much shorter Imprint blades are")
    imprint_thickness: float = Field(0.8, ge=0.4, le=5)
    support: Literal["bridges", "plate"] = "bridges"
    bridge_width: float = Field(3.0, ge=1, le=20)
    min_hole: float = Field(8.0, ge=0, le=100, description="Holes narrower than this are dropped")
    min_imprint: float = Field(2.0, ge=0, le=50, description="Imprint pieces smaller than this are dropped")


class TraceParams(BaseModel):
    ink: str = Field("#000000", description='Ink colour as "#rrggbb", or "alpha" for opaque pixels')
    tolerance: float = Field(0.35, ge=0, le=1, description="Colour distance still counted as Ink")
    invert: bool = False
    smoothing: float = Field(1.0, ge=0, le=10, description="Outline simplification in pixels")


class FilamentParams(BaseModel):
    material: Material = Material.PLA
    price_per_kg: float | None = Field(None, ge=0)
    diameter: float = Field(1.75, gt=0)


class Feature(BaseModel):
    """A region or line of the picture that can be given a Role."""

    id: str
    kind: Literal["region", "line"]
    role: Role
    default_role: Role
    path: str  # SVG path data in mm, picture orientation
    area: float


class FilamentEstimate(BaseModel):
    material: Material
    volume_cm3: float
    grams: float
    metres: float
    cost: float | None


class Dimensions(BaseModel):
    width: float
    depth: float
    height: float
