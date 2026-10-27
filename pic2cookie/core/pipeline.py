"""Picture in, Cutter out: the whole core in one call."""

from dataclasses import dataclass

from pic2cookie.core import filament
from pic2cookie.core.cutter import Cutter, build
from pic2cookie.core.model import (
    CutterParams,
    FilamentEstimate,
    FilamentParams,
    Role,
    TraceParams,
)
from pic2cookie.core.outline import parse_svg
from pic2cookie.core.roles import Layout, layout, to_marked_svg
from pic2cookie.core.trace import is_svg, trace


@dataclass
class Result:
    svg: str  # the picture as SVG (traced, if it was a raster)
    layout: Layout
    cutter: Cutter
    estimate: FilamentEstimate

    @property
    def marked_svg(self) -> str:
        return to_marked_svg(self.layout)


def to_svg(data: bytes, trace_params: TraceParams | None = None) -> str:
    if is_svg(data):
        return data.decode("utf-8", errors="replace")
    return trace(data, trace_params)


def make(
    data: bytes,
    cutter_params: CutterParams | None = None,
    trace_params: TraceParams | None = None,
    filament_params: FilamentParams | None = None,
    roles: dict[str, Role] | None = None,
) -> Result:
    cutter_params = cutter_params or CutterParams()
    svg = to_svg(data, trace_params)
    drawing = parse_svg(svg)  # traced SVGs are black; any non-white colour counts in others
    shapes = layout(drawing, cutter_params, roles)
    cutter = build(shapes, cutter_params)
    estimate = filament.estimate(cutter.volume_mm3, filament_params or FilamentParams())
    return Result(svg, shapes, cutter, estimate)
