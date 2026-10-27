"""Cutter mesh in, file bytes out."""

import json
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from pathlib import Path

from pic2cookie.core.model import Material

PROFILES = Path(__file__).parent / "bambu_profiles"


class Format(StrEnum):
    STL = "stl"
    THREEMF = "3mf"
    BAMBU = "bambu"

    @property
    def filename(self) -> str:
        return {"stl": "cutter.stl", "3mf": "cutter.3mf", "bambu": "cutter.bambu.3mf"}[self]

    @property
    def media_type(self) -> str:
        return "model/stl" if self is Format.STL else "model/3mf"


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
        raise ValueError(f"Unknown printer {printer_id!r}; choose one of {', '.join(PRINTER_ORDER)}")
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


def export(
    mesh,
    fmt: Format,
    *,
    name: str = "cutter",
    printer_id: str = DEFAULT_PRINTER,
    material: Material = Material.PLA,
) -> bytes:
    match fmt:
        case Format.STL:
            from pic2cookie.core.export.stl import to_stl

            return to_stl(mesh)
        case Format.THREEMF:
            from pic2cookie.core.export.threemf import to_3mf

            return to_3mf(mesh, name)
        case Format.BAMBU:
            from pic2cookie.core.export.bambu import to_bambu_3mf

            return to_bambu_3mf(mesh, name, printer_id, material)
