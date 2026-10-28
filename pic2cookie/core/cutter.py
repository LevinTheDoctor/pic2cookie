"""Silhouette and Features in, Cutter out.

Everything is built from 2D regions, then extruded into stacked prisms
(ADR-0002). The Cutter is modelled flange-down in print orientation. Picture
coordinates (y down) are used unchanged as x/y on the plate. Seen from above,
that mirrors the picture, so the cookie is the right way round once the
cutter is flipped to cut.
"""

from dataclasses import dataclass, field

lazy import shapely
lazy from shapely import affinity
lazy from shapely.geometry import Polygon
lazy from shapely.ops import nearest_points

from pic2cookie.core.model import CutterParams, Dimensions, Notice, Role
from pic2cookie.core.roles import Layout, clean, polygons, stroke_width
from pic2cookie.core.solid import Layer, Part, centre, extrude, volume


@dataclass
class Cutter:
    mesh: object  # trimesh.Trimesh, centred on x/y, standing on z=0
    layers: list[Layer]
    dimensions: Dimensions
    warnings: list[str] = field(default_factory=list)

    @property
    def volume_mm3(self) -> float:
        return volume(self.layers)

    @property
    def parts(self) -> list[Part]:
        return [Part("cutter", self.layers, self.mesh)]


def build(result: Layout, params: CutterParams) -> Cutter:
    warnings = list(result.warnings)
    t = params.blade_thickness
    silhouette = result.silhouette
    holes = clean(shapely.union_all(result.by_role(Role.HOLE) or [Polygon()]))
    cookie = clean(silhouette.difference(holes))

    outer_blade = clean(silhouette.buffer(t, quad_segs=8).difference(silhouette))
    outer_flange = clean(silhouette.buffer(t + params.flange_width, quad_segs=8).difference(silhouette))
    inner_blades = clean(holes.difference(holes.buffer(-t, quad_segs=8)))
    inner_flanges = clean(holes.difference(holes.buffer(-(t + params.flange_width), quad_segs=8)))
    imprints = clean(_imprints(result, params).intersection(cookie))

    if params.support == "plate":
        support = cookie
    else:
        anchored = clean(outer_blade.union(outer_flange))
        floating = clean(shapely.union_all([inner_blades, inner_flanges, imprints]))
        support = _bridges(anchored, floating, params.bridge_width, silhouette.buffer(t, quad_segs=8))

    blades = clean(outer_blade.union(inner_blades))
    imprint_top = params.blade_height - params.imprint_offset
    if not imprints.is_empty and imprint_top <= params.flange_height:
        warnings.append(
            Notice("imprint_offset_too_big", "The imprint offset leaves no Imprint blade above the Flange.")
        )
        imprints = Polygon()

    gaps = silhouette.buffer(t).buffer(-t).difference(silhouette)
    if any(g.area > 2 * t * t for g in polygons(gaps)):  # ignore fillets in concave corners
        text = f"Gaps narrower than {2 * t:.1f} mm between parts of the shape will print solid."
        warnings.append(Notice("gaps_solid", text, mm=round(2 * t, 1)))

    base = clean(shapely.union_all([outer_flange, inner_flanges, support, blades, imprints]))
    layers = [Layer(base, 0.0, params.flange_height)]
    if not imprints.is_empty:
        layers.append(Layer(clean(blades.union(imprints)), params.flange_height, imprint_top))
        layers.append(Layer(blades, imprint_top, params.blade_height))
    else:
        layers.append(Layer(blades, params.flange_height, params.blade_height))
    layers = [layer for layer in layers if not layer.region.is_empty and layer.z1 > layer.z0]

    mesh = extrude(layers)
    centre([mesh])
    minx, miny, maxx, maxy = base.bounds
    dims = Dimensions(width=round(maxx - minx, 2), depth=round(maxy - miny, 2), height=params.blade_height)
    return Cutter(mesh, layers, dims, warnings)


def _imprints(result: Layout, params: CutterParams):
    t = params.imprint_thickness
    parts = []
    for region in result.by_role(Role.IMPRINT, "region"):
        if stroke_width(region) < 3 * t:
            parts.append(_thin_to(region, t))  # a thin gap in the Ink reads as a line
        else:
            parts.append(region.boundary.buffer(t / 2, quad_segs=4))
    for line in result.by_role(Role.IMPRINT, "line"):
        parts.append(_thin_to(line, t))
    return shapely.union_all(parts) if parts else Polygon()


def _thin_to(line, t: float):
    """A strip `t` wide along the middle of a drawn line."""
    width = stroke_width(line)
    if width <= t:
        return line.buffer((t - width) / 2, quad_segs=4)
    strip = line.buffer(-(width - t) / 2, quad_segs=4).buffer(0)
    expected = t * line.length / 2
    if strip.is_empty or strip.area < 0.3 * expected:
        return line  # too uneven to thin; keep the line as drawn
    return strip


def _bridges(anchored, floating, width: float, within):
    """Bars at Flange height joining each floating piece to its nearest anchored piece."""
    pieces = sorted(polygons(floating), key=lambda p: anchored.distance(p))
    bars = []
    attached = anchored
    remaining = [p for p in pieces if not p.intersects(anchored)]
    while remaining:
        remaining.sort(key=lambda p: attached.distance(p))
        piece = remaining.pop(0)
        a, b = nearest_points(piece, attached)
        bar = shapely.LineString([a, b])
        if bar.length < 1e-6:
            continue
        bar = affinity.scale(bar, 1 + width / bar.length, 1 + width / bar.length)
        bars.append(bar.buffer(width / 2, cap_style="flat").intersection(within))
        attached = attached.union(piece).union(bars[-1])
    return clean(shapely.union_all(bars)) if bars else Polygon()
