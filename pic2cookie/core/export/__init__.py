"""Parts of a Cutter or Coaster in, file bytes out."""

import json
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from pathlib import Path

from pic2cookie.core.model import CodedError, Dimensions, Material, Notice, Product
from pic2cookie.core.solid import Part

PROFILES = Path(__file__).parent / "bambu_profiles"


class Format(StrEnum):
    STL = "stl"
    THREEMF = "3mf"
    BAMBU = "bambu"

    def filename(self, product: Product = Product.CUTTER) -> str:
        """A Coaster's STL is a zip with one STL per coloured part."""
        suffix = {"stl": ".stl", "3mf": ".3mf", "bambu": ".bambu.3mf"}[self]
        if self is Format.STL and product is Product.COASTER:
            suffix = ".stl.zip"
        return f"{product.value}{suffix}"


@dataclass(frozen=True)
class Printer:
    id: str
    name: str
    bed: tuple[float, float]
    height: float
    materials: tuple[Material, ...]


PRINTER_ORDER = ("a1mini", "a1", "p1s", "p2s", "x1c", "h2d")
DEFAULT_PRINTER = "a1mini"


@cache
def profile(printer_id: str) -> dict:
    path = PROFILES / f"{printer_id}.json"
    if printer_id not in PRINTER_ORDER or not path.exists():
        raise CodedError(
            "unknown_printer",
            f"Unknown printer {printer_id!r}; choose one of {', '.join(PRINTER_ORDER)}",
            printer=printer_id,
        )
    return json.loads(path.read_text())


@cache
def printers() -> tuple[Printer, ...]:
    result = []
    for pid in PRINTER_ORDER:
        p = profile(pid)
        xs, ys = zip(*(map(float, pt.split("x")) for pt in p["bed"]), strict=True)
        materials = tuple(m for m in Material if m.value in p["filaments"])
        bed = (max(xs) - min(xs), max(ys) - min(ys))
        result.append(Printer(pid, p["printer_model"], bed, float(p["height"]), materials))
    return tuple(result)


def printer(printer_id: str) -> Printer:
    for p in printers():
        if p.id == printer_id:
            return p
    profile(printer_id)  # raises with the list of known printers
    raise AssertionError


def bed_warning(dimensions: Dimensions, printer_id: str) -> str | None:
    p = printer(printer_id)
    fits = (dimensions.width <= p.bed[0] and dimensions.depth <= p.bed[1]) or (
        dimensions.depth <= p.bed[0] and dimensions.width <= p.bed[1]
    )
    if fits and dimensions.height <= p.height:
        return None
    return Notice(
        "too_big_for_bed",
        f"At {dimensions.width:g} x {dimensions.depth:g} mm it does not fit the {p.name}'s bed.",
        width=dimensions.width,
        depth=dimensions.depth,
        printer=p.name,
    )


def export(
    parts: list[Part] | object,
    fmt: Format,
    *,
    name: str = "cutter",
    product: Product = Product.CUTTER,
    printer_id: str = DEFAULT_PRINTER,
    material: Material = Material.PLA,
    pause_z: float | None = None,
) -> bytes:
    """`parts` may also be a single mesh. `pause_z` adds a pause to the Bambu project."""
    if not isinstance(parts, list):
        parts = [Part(product.value, [], parts)]
    match fmt:
        case Format.STL:
            from pic2cookie.core.export.stl import to_stl, to_stl_zip

            return to_stl_zip(parts) if product is Product.COASTER else to_stl(parts[0].mesh)
        case Format.THREEMF:
            from pic2cookie.core.export.threemf import to_3mf

            return to_3mf(parts, name)
        case Format.BAMBU:
            from pic2cookie.core.export.bambu import to_bambu_3mf

            return to_bambu_3mf(parts, name, printer_id, material, pause_z)
