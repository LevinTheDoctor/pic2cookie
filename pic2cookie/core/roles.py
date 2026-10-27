"""Ink to Silhouette and Features, each with a Role.

All geometry here is in mm, in picture orientation (y pointing down).
"""

from dataclasses import dataclass, field

lazy import shapely
lazy from shapely import affinity
lazy from shapely.geometry import MultiPolygon, Polygon

from pic2cookie.core.model import CutterParams, Feature, Role
from pic2cookie.core.outline import Drawing

# Ink covering at least this share of the Silhouette makes a filled drawing.
FILLED_RATIO = 0.5
# Areas below this (mm²) are noise from tracing or sampling.
NOISE_AREA = 0.05


@dataclass
class FeatureShape:
    feature: Feature
    geometry: object


@dataclass
class Layout:
    silhouette: object  # Polygon
    features: list[FeatureShape]
    style: str  # "filled" | "line"
    warnings: list[str] = field(default_factory=list)

    def by_role(self, role: Role, kind: str | None = None) -> list[object]:
        return [
            f.geometry
            for f in self.features
            if f.feature.role is role and (kind is None or f.feature.kind == kind)
        ]


def polygons(geom) -> list:
    """The non-empty polygons in any shapely geometry."""
    if geom is None or geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    if hasattr(geom, "geoms"):
        return [p for g in geom.geoms for p in polygons(g)]
    return []


def clean(geom):
    """Valid polygons only, without slivers."""
    if geom.is_empty:
        return Polygon()
    geom = shapely.make_valid(geom)
    return shapely.union_all([p for p in polygons(geom) if p.area > NOISE_AREA] or [Polygon()])


def stroke_width(poly) -> float:
    """Estimated width of a long thin shape: area / half its perimeter."""
    return 2 * poly.area / poly.length if poly.length else 0.0


def path_data(geom) -> str:
    """SVG path data for polygons (rings closed with Z)."""
    parts = []
    for poly in polygons(geom):
        for ring in (poly.exterior, *poly.interiors):
            coords = list(ring.coords)[:-1]
            parts.append("M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in coords) + "Z")
    return "".join(parts)


def _largest(geom, warnings: list[str]):
    polys = sorted(polygons(geom), key=lambda p: -p.area)
    if not polys:
        raise ValueError("Nothing to make a cutter from")
    if len(polys) > 1 and polys[1].area > 0.01 * polys[0].area:
        warnings.append(f"The picture has {len(polys)} separate shapes; only the largest is used.")
    return Polygon(polys[0].exterior)


def _scaled(drawing: Drawing, size: float):
    """Scale and move the drawing so its Silhouette's longest side is `size` mm."""
    silhouette = _largest(drawing.ink, [])
    minx, miny, maxx, maxy = silhouette.bounds
    factor = size / max(maxx - minx, maxy - miny)

    def fit(geom):
        geom = affinity.translate(geom, -minx, -miny)
        return affinity.scale(geom, factor, factor, origin=(0, 0))

    return fit


def layout(drawing: Drawing, params: CutterParams, overrides: dict[str, Role] | None = None) -> Layout:
    fit = _scaled(drawing, params.size)
    if drawing.marked:
        return _marked_layout(drawing, fit, params)
    warnings: list[str] = []
    ink = clean(fit(drawing.ink).simplify(0.01))
    silhouette = _largest(shapely.union_all([Polygon(p.exterior) for p in polygons(ink)]), warnings)
    inside = clean(ink.intersection(silhouette))
    style = "filled" if inside.area >= FILLED_RATIO * silhouette.area else "line"

    shapes: list[tuple[str, object, Role]] = []
    for region in _ordered(clean(silhouette.difference(inside))):
        if style == "filled":
            role = Role.HOLE if _fits(region, params.min_hole) else Role.IMPRINT
        else:
            role = Role.IGNORE
        shapes.append(("region", region, role))
    if style == "line":
        width = stroke_width(_ordered(inside)[0]) if not inside.is_empty else 0
        band = silhouette.difference(silhouette.buffer(-1.5 * max(width, 0.1)))
        for line in _ordered(clean(inside.difference(band))):
            shapes.append(("line", line, Role.IMPRINT))

    features = []
    counters = {"region": 0, "line": 0}
    for kind, geom, default in shapes:
        counters[kind] += 1
        fid = f"{kind[0]}{counters[kind]}"
        role = (overrides or {}).get(fid, default)
        if kind == "line" and role is Role.HOLE:
            role = default
        features.append(
            FeatureShape(
                Feature(
                    id=fid,
                    kind=kind,
                    role=role,
                    default_role=default,
                    path=path_data(geom),
                    area=round(geom.area, 2),
                ),
                geom,
            )
        )
    result = Layout(silhouette, features, style, warnings)
    _drop_small(result, params)
    return result


def _ordered(geom) -> list:
    """Polygons in a stable order: largest first, then by position."""
    return sorted(
        polygons(geom), key=lambda p: (-round(p.area, 1), round(p.centroid.x, 1), round(p.centroid.y, 1))
    )


def _fits(poly, width: float) -> bool:
    """Whether the shape is at least `width` wide somewhere."""
    return width <= 0 or not poly.buffer(-width / 2).is_empty


def _drop_small(result: Layout, params: CutterParams) -> None:
    """Apply `min_hole` and `min_imprint`, saying what changed."""
    narrow_holes = dropped_imprints = 0
    for fs in result.features:
        f = fs.feature
        if f.role is Role.HOLE and not _fits(fs.geometry, params.min_hole):
            result.warnings.append(
                f"Hole {f.id} is narrower than {params.min_hole:g} mm; the dough may not come out of it."
            )
        elif (
            f.default_role is Role.IMPRINT
            and f.kind == "region"
            and result.style == "filled"
            and fs.geometry.area >= (params.min_hole / 2) ** 2
        ):
            narrow_holes += 1
        if f.role is Role.IMPRINT:
            minx, miny, maxx, maxy = fs.geometry.bounds
            if max(maxx - minx, maxy - miny) < params.min_imprint:
                f.role = Role.IGNORE
                dropped_imprints += 1
    if narrow_holes:
        result.warnings.append(
            f"{narrow_holes} hole(s) narrower than {params.min_hole:g} mm became Imprint blades."
        )
    if dropped_imprints:
        result.warnings.append(
            f"Dropped {dropped_imprints} imprint(s) smaller than {params.min_imprint:g} mm."
        )


def _marked_layout(drawing: Drawing, fit, params: CutterParams) -> Layout:
    warnings: list[str] = []
    silhouette = _largest(fit(drawing.ink), warnings)
    features = []
    counters = {"region": 0, "line": 0}
    for m in drawing.marked:
        if m.role is Role.OUTER:
            continue
        kind = "line" if m.kind == "line" else "region"
        counters[kind] += 1
        geom = clean(fit(m.geometry))
        features.append(
            FeatureShape(
                Feature(
                    id=m.feature_id or f"{kind[0]}{counters[kind]}",
                    kind=kind,
                    role=m.role,
                    default_role=m.role,
                    path=path_data(geom),
                    area=round(geom.area, 2),
                ),
                geom,
            )
        )
    return Layout(silhouette, features, "marked", warnings)


def to_marked_svg(result: Layout) -> str:
    """The Layout as a role-marked SVG that `parse_svg` reads back unchanged."""
    minx, miny, maxx, maxy = result.silhouette.bounds
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{minx:.2f} {miny:.2f} {maxx - minx:.2f} {maxy - miny:.2f}" '
        f'width="{maxx - minx:.2f}mm" height="{maxy - miny:.2f}mm">',
        f'<path data-role="outer" fill="#000" d="{path_data(result.silhouette)}"/>',
    ]
    colours = {Role.HOLE: "#fff", Role.IMPRINT: "#888", Role.IGNORE: "none"}
    for fs in result.features:
        f = fs.feature
        out.append(
            f'<path data-role="{f.role}" data-kind="{f.kind}" data-feature-id="{f.id}" '
            f'fill="{colours[f.role]}" fill-rule="evenodd" d="{f.path}"/>'
        )
    out.append("</svg>")
    return "\n".join(out)
