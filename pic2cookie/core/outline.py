"""SVG in, Ink out: the drawn area of an SVG as shapely polygons.

Coordinates stay in the SVG's user space (y pointing down); scaling to mm
happens later, once the Silhouette is known.
"""

import math
import re
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

lazy import numpy as np
lazy import shapely
lazy from shapely.geometry import LineString, Polygon
lazy from svgpathtools import parse_path
lazy from svgpathtools import path as svgpath
lazy from svgpathtools.parser import parse_transform
lazy from svgpathtools.svg_to_paths import (
    ellipse2pathd,
    polygon2pathd,
    polyline2pathd,
    rect2pathd,
)

from pic2cookie.core.model import CodedError, Role

SKIPPED_TAGS = {
    "defs",
    "clipPath",
    "mask",
    "symbol",
    "marker",
    "pattern",
    "style",
    "title",
    "desc",
    "metadata",
    "text",
}
INHERITED = (
    "fill",
    "stroke",
    "stroke-width",
    "fill-rule",
    "fill-opacity",
    "stroke-opacity",
    "opacity",
    "visibility",
    "display",
)

NAMED_COLOURS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "brown": (165, 42, 42),
    "pink": (255, 192, 203),
    "purple": (128, 0, 128),
}


class SvgError(CodedError):
    pass


@dataclass
class MarkedShape:
    """An element of a role-marked SVG (see `roles.to_marked_svg`)."""

    role: Role
    kind: str
    geometry: object
    feature_id: str | None = None


@dataclass
class Drawing:
    ink: object  # shapely (Multi)Polygon
    marked: list[MarkedShape] = field(default_factory=list)


def parse_colour(value: str | None) -> tuple[int, int, int] | None:
    """Return RGB for an SVG paint value, or None for no paint."""
    if value is None:
        return None
    value = value.strip().lower()
    if value in ("none", "transparent", ""):
        return None
    if value.startswith("url("):
        return (0, 0, 0)  # gradients and patterns count as Ink
    if value.startswith("#"):
        hex_ = value[1:]
        if len(hex_) in (3, 4):
            hex_ = "".join(c * 2 for c in hex_[:3])
        try:
            return tuple(int(hex_[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return (0, 0, 0)
    if m := re.match(r"rgba?\(([^)]*)\)", value):
        parts = [p.strip() for p in m.group(1).replace("/", ",").split(",")]
        rgb = []
        for p in parts[:3]:
            rgb.append(round(float(p[:-1]) * 2.55) if p.endswith("%") else round(float(p)))
        return tuple(rgb)
    return NAMED_COLOURS.get(value, (0, 0, 0))


def is_ink(rgb: tuple[int, int, int], ink: tuple[int, int, int] | None, tolerance: float) -> bool:
    """Whether a paint colour counts as Ink; `ink=None` means any non-white colour."""
    if ink is None:
        luminance = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255
        return luminance < 0.92
    return colour_distance(rgb, ink) <= tolerance


def colour_distance(a, b) -> float:
    return math.dist(a, b) / math.dist((0, 0, 0), (255, 255, 255))


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _style(element) -> dict[str, str]:
    style = {k: element.get(k) for k in INHERITED if element.get(k) is not None}
    for decl in (element.get("style") or "").split(";"):
        if ":" in decl:
            key, value = decl.split(":", 1)
            style[key.strip()] = value.strip()
    return style


def _path_d(element, tag: str) -> str | None:
    attrs = dict(element.attrib)
    try:
        match tag:
            case "path":
                return attrs.get("d")
            case "rect":
                attrs.setdefault("x", "0")
                attrs.setdefault("y", "0")
                return rect2pathd(attrs)
            case "circle" | "ellipse":
                return ellipse2pathd(attrs)
            case "line":
                return "M{} {}L{} {}".format(*(attrs.get(k, "0") for k in ("x1", "y1", "x2", "y2")))
            case "polyline":
                return polyline2pathd(attrs.get("points", ""))
            case "polygon":
                return polygon2pathd(attrs.get("points", ""))
    except KeyError, ValueError:
        return None
    return None


def _number(value: str | None, default: float) -> float:
    if value is None:
        return default
    m = re.match(r"\s*([-+]?\d*\.?\d+(?:e[-+]?\d+)?)", value)
    return float(m.group(1)) if m else default


@dataclass
class _Shape:
    rings: list  # list of Nx2 point arrays, one per subpath
    closed: list[bool]
    style: dict[str, str]
    stroke_scale: float
    attrs: dict[str, str]


def _walk(element, transform, style, out: list[_Shape]) -> None:
    tag = _local(element.tag)
    if tag in SKIPPED_TAGS:
        return
    style = style | _style(element)
    if style.get("display") == "none" or style.get("visibility") == "hidden":
        return
    transform = transform @ parse_transform(element.get("transform"))
    if tag in ("svg", "g", "a", "switch"):
        for child in element:
            _walk(child, transform, style, out)
        return
    d = _path_d(element, tag)
    if not d:
        return
    try:
        path = svgpath.transform(parse_path(d), transform)
    except ValueError, IndexError:
        return
    if len(path) == 0:
        return
    rings, closed = [], []
    for sub in path.continuous_subpaths():
        pts = _sample(sub)
        if len(pts) >= 2:
            rings.append(pts)
            closed.append(sub.isclosed() or tag != "path" and tag not in ("line", "polyline"))
    scale = math.sqrt(abs(np.linalg.det(transform[:2, :2])))
    attrs = {k: v for k, v in element.attrib.items() if k.startswith("data-")}
    out.append(_Shape(rings, closed, style, scale, attrs))


def _sample(path) -> np.ndarray:
    pts = []
    for seg in path:
        name = type(seg).__name__
        n = 1 if name == "Line" else max(8, min(256, math.ceil(seg.length(error=1e-4) / 0.5)))
        ts = np.linspace(0, 1, n + 1)[:-1]
        pts.extend(seg.point(t) for t in ts)
    pts.append(path[-1].end)
    arr = np.array([[p.real, p.imag] for p in pts])
    keep = np.ones(len(arr), bool)
    keep[1:] = np.any(np.abs(np.diff(arr, axis=0)) > 1e-9, axis=1)
    return arr[keep]


def _fill_geometry(shape: _Shape):
    """Fill area of a shape, honouring the fill rule."""
    rings = []
    for pts in shape.rings:
        if len(pts) < 3:
            continue
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = shapely.make_valid(poly)
        if poly.area <= 1e-12:
            continue
        signed = float(np.sum(pts[:-1, 0] * pts[1:, 1] - pts[1:, 0] * pts[:-1, 1]))
        rings.append((poly, 1 if signed > 0 else -1))
    rings.sort(key=lambda r: -r[0].area)
    evenodd = shape.style.get("fill-rule", "nonzero") == "evenodd"
    result = Polygon()
    for i, (poly, sign) in enumerate(rings):
        containers = [s for p, s in rings[:i] if p.buffer(1e-9).contains(poly)]
        if evenodd:
            filled_out, filled_in = len(containers) % 2 == 1, len(containers) % 2 == 0
        else:
            w = sum(containers)
            filled_out, filled_in = w != 0, w + sign != 0
        if filled_in and not filled_out:
            result = result.union(poly)
        elif filled_out and not filled_in:
            result = result.difference(poly)
    return result


def _stroke_geometry(shape: _Shape):
    width = _number(shape.style.get("stroke-width"), 1.0) * shape.stroke_scale
    if width <= 0:
        return Polygon()
    lines = []
    for pts, closed in zip(shape.rings, shape.closed, strict=True):
        if closed and len(pts) > 2 and not np.allclose(pts[0], pts[-1]):
            pts = np.vstack([pts, pts[:1]])
        lines.append(LineString(pts))
    return shapely.union_all([ln.buffer(width / 2, quad_segs=4) for ln in lines])


def _opaque(style: dict[str, str], key: str) -> bool:
    return _number(style.get("opacity"), 1) > 0.05 and _number(style.get(key), 1) > 0.05


def parse_svg(data: bytes | str, ink: str | None = None, tolerance: float = 0.35) -> Drawing:
    """Parse SVG markup into a Drawing.

    Shapes are painted in document order: Ink-coloured fills and strokes add
    to the Ink, background-coloured ones (white, by default) cut it away.
    `ink` restricts Ink to one "#rrggbb" colour; by default any non-white
    colour counts.
    """
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise SvgError("svg_invalid", f"Not a valid SVG: {e}", detail=str(e)) from e
    if _local(root.tag) != "svg":
        raise SvgError("svg_invalid", "Not an SVG document", detail="")
    ink_rgb = parse_colour(ink) if ink else None
    shapes: list[_Shape] = []
    _walk(root, np.identity(3), {"fill": "black"}, shapes)

    marked = [s for s in shapes if "data-role" in s.attrs]
    if marked:
        return _marked_drawing(marked)

    drawn = Polygon()
    for shape in shapes:
        layers = []
        fill = parse_colour(shape.style.get("fill"))
        if fill is not None and _opaque(shape.style, "fill-opacity"):
            layers.append((fill, _fill_geometry(shape)))
        stroke = parse_colour(shape.style.get("stroke"))
        if stroke is not None and _opaque(shape.style, "stroke-opacity"):
            layers.append((stroke, _stroke_geometry(shape)))
        for colour, geom in layers:
            if geom.is_empty:
                continue
            if is_ink(colour, ink_rgb, tolerance):
                drawn = drawn.union(geom)
            else:
                drawn = drawn.difference(geom)
    if drawn.is_empty:
        raise SvgError("no_ink", "The SVG contains no Ink")
    return Drawing(ink=shapely.make_valid(drawn))


def _marked_drawing(shapes: list[_Shape]) -> Drawing:
    marked = []
    for shape in shapes:
        try:
            role = Role(shape.attrs["data-role"])
        except ValueError as e:
            role = shape.attrs["data-role"]
            raise SvgError("svg_bad_role", f"Unknown data-role {role!r}", role=role) from e
        geom = _fill_geometry(shape)
        if geom.is_empty:
            continue
        marked.append(
            MarkedShape(
                role, shape.attrs.get("data-kind", "region"), geom, shape.attrs.get("data-feature-id")
            )
        )
    outer = [m for m in marked if m.role is Role.OUTER]
    if not outer:
        raise SvgError("svg_no_outer", 'A role-marked SVG needs an element with data-role="outer"')
    return Drawing(ink=shapely.union_all([m.geometry for m in outer]), marked=marked)
