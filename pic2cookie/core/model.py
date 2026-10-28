"""Parameters and results shared by the core, the CLI and the API (lengths in mm)."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Notice(str):
    """A warning or error in English that also carries a code and parameters,
    so the frontend can show it in the user's language."""

    code: str
    params: dict[str, float | int | str]

    def __new__(cls, code: str, text: str, **params: float | int | str) -> Notice:
        notice = super().__new__(cls, text)
        notice.code = code
        notice.params = params
        return notice


class CodedError(ValueError):
    """A ValueError whose message is a Notice."""

    def __init__(self, code: str, text: str, **params: float | int | str):
        super().__init__(text)
        self.notice = Notice(code, text, **params)


class Message(BaseModel):
    """A Notice as stored and sent: `text` is English, `code` and `params` translate it."""

    code: str = "text"
    params: dict[str, float | int | str] = {}
    text: str

    @classmethod
    def of(cls, value: str | Notice | Exception) -> Message:
        if isinstance(value, CodedError):
            value = value.notice
        if isinstance(value, Notice):
            return cls(code=value.code, params=value.params, text=str(value))
        return cls(text=str(value))


class Product(StrEnum):
    CUTTER = "cutter"
    COASTER = "coaster"


class Role(StrEnum):
    OUTER = "outer"
    HOLE = "hole"
    IMPRINT = "imprint"
    MOTIF = "motif"
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


class Coin(StrEnum):
    EUR2 = "eur2"
    EUR1 = "eur1"
    EUR050 = "eur050"
    USD025 = "usd025"
    CUSTOM = "custom"


# diameter, thickness in mm
COINS: dict[Coin, tuple[float, float]] = {
    Coin.EUR2: (25.75, 2.20),
    Coin.EUR1: (23.25, 2.33),
    Coin.EUR050: (24.25, 2.38),
    Coin.USD025: (24.26, 1.75),
}


class CoasterParams(BaseModel):
    shape: Literal["round", "square", "rounded", "silhouette"] = "round"
    size: float = Field(100.0, ge=30, le=300, description="Diameter or side of the Plate")
    thickness: float = Field(4.0, ge=2, le=12)
    corner_radius: float = Field(10.0, ge=0, le=100, description="For the rounded square")
    margin: float = Field(10.0, ge=0, le=50, description="Space between the Motif and the edge")
    motif_scale: float = Field(1.0, gt=0, le=1, description="Share of the largest Motif that fits")
    motif_style: Literal["inlay", "raised", "engraved"] = "inlay"
    motif_depth: float = Field(0.6, ge=0.2, le=3, description="Inlay or engraving depth, or raised height")
    invert: bool = Field(False, description="The background becomes the Motif")
    min_line: float = Field(0.5, ge=0, le=3, description="Thinner Motif lines are widened to this")
    plate_colour: str = Field("#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")
    motif_colour: str = Field("#000000", pattern=r"^#[0-9a-fA-F]{6}$")
    rim: bool = False
    rim_width: float = Field(3.0, ge=1, le=20)
    rim_height: float = Field(1.0, ge=0.2, le=5)
    feet: bool = Field(False, description="Foot recesses for stick-on pads")
    foot_diameter: float = Field(10.0, ge=4, le=30)
    foot_depth: float = Field(1.0, ge=0.4, le=3)
    opener: Literal["none", "coin", "plastic"] = "none"
    opener_side: Literal["right", "left", "top", "bottom"] = "right"
    opener_thickness: float = Field(6.0, ge=4, le=15)
    coin: Coin = Coin.EUR2
    coin_diameter: float = Field(25.75, ge=15, le=40, description="For a custom coin")
    coin_thickness: float = Field(2.2, ge=1, le=4, description="For a custom coin")

    def coin_size(self) -> tuple[float, float]:
        return COINS.get(self.coin, (self.coin_diameter, self.coin_thickness))


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


class PartEstimate(BaseModel):
    """The Filament estimate of one coloured part of a Product."""

    name: str
    colour: str | None
    estimate: FilamentEstimate


class Dimensions(BaseModel):
    width: float
    depth: float
    height: float
