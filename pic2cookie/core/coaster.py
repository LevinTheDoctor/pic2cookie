"""Ink in, Coaster out: a Plate with the Motif on top, optionally a Rim, Foot
recesses and a Bottle opener.

Like the Cutter, everything is 2D regions extruded into stacked prisms
(ADR-0002). Layout happens in picture orientation (y down, as the picture
view shows it). The Coaster is printed face up, so y is flipped on extrusion
and the Motif reads the right way round from above.
"""

import math
from dataclasses import dataclass, field

lazy import shapely
lazy from shapely import affinity
lazy from shapely.geometry import Point, Polygon, box
lazy from shapely.ops import nearest_points

from pic2cookie.core.model import CoasterParams, CodedError, Dimensions, Feature, Notice, Role
from pic2cookie.core.outline import Drawing
from pic2cookie.core.roles import FeatureShape, _ordered, clean, path_data, polygons, stroke_width
from pic2cookie.core.solid import Layer, Part, centre, extrude, stack

# Bambu's "0.20mm Standard" process; the coin slot is aligned to its layers.
LAYER = 0.2
COIN_FLOOR = 1.2  # plastic under the coin
COIN_PLAY = 0.4  # extra diameter of the slot
COIN_SHOW = 3.0  # how far the coin's edge reaches into the opening
CAP_REACH = 24.0  # from the catching edge to the far end of the opening
OPENING_WIDTH = 34.0  # a crown cap is about 32 mm across
MIN_PIECE = 1.0  # mm²; smaller Motif pieces are dropped
DIRECTIONS = {"right": (1, 0), "left": (-1, 0), "top": (0, -1), "bottom": (0, 1)}


@dataclass
class Opener:
    tab: object  # the tab's outline, overlapping the Plate
    opening: object  # the hole the cap goes into
    pocket: object  # the coin slot, or empty


@dataclass
class CoasterLayout:
    plate: object  # the Plate without the Bottle opener
    inner: object  # where the Motif may go
    features: list[FeatureShape]
    opener: Opener | None
    feet: object
    warnings: list[str] = field(default_factory=list)
    style: str = "coaster"

    @property
    def motif(self):
        pieces = [f.geometry for f in self.features if f.feature.role is Role.MOTIF]
        return clean(shapely.union_all(pieces)) if pieces else Polygon()

    @property
    def body(self):
        """The Plate joined with the Bottle opener's tab, minus its opening."""
        if not self.opener:
            return self.plate
        joined = shapely.union(self.plate, self.opener.tab).buffer(4, quad_segs=8).buffer(-4, quad_segs=8)
        return clean(joined.difference(self.opener.opening))


@dataclass
class Coaster:
    parts: list[Part]
    dimensions: Dimensions
    warnings: list[str]
    pause_z: float | None = None  # insert the coin when the layer ending here starts

    @property
    def volume_mm3(self) -> float:
        return sum(p.volume_mm3 for p in self.parts)


def _normalised(ink):
    """The Ink centred on the origin with its longest side 100."""
    minx, miny, maxx, maxy = ink.bounds
    factor = 100 / max(maxx - minx, maxy - miny)
    ink = affinity.translate(ink, -(minx + maxx) / 2, -(miny + maxy) / 2)
    return affinity.scale(ink, factor, factor, origin=(0, 0))


def _plate(params: CoasterParams):
    half = params.size / 2
    match params.shape:
        case "round":
            return Point(0, 0).buffer(half, quad_segs=32)
        case "square":
            return box(-half, -half, half, half)
        case _:
            r = min(params.corner_radius, half - 0.01)
            return box(-half + r, -half + r, half - r, half - r).buffer(r, quad_segs=16)


def _one_piece(geom, warnings: list[str]):
    """Join separate pieces of a Silhouette Plate, closing gaps as needed."""
    for k in (2, 5, 10, 20, 40):
        if len(polygons(geom)) <= 1:
            return geom
        geom = geom.buffer(k, quad_segs=8).buffer(-k, quad_segs=8)
    if len(polygons(geom)) > 1:
        text = "The picture's parts are far apart; the Plate follows their outline loosely."
        warnings.append(Notice("parts_far_apart", text))
        geom = geom.convex_hull
    return geom


def _fit(shape, inner) -> float:
    """The largest scale at which `shape` (around the origin) fits inside `inner`."""
    hull = shape.convex_hull
    lo, hi = 0.0, 10.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if inner.contains(affinity.scale(hull, mid, mid, origin=(0, 0))):
            lo = mid
        else:
            hi = mid
    return lo


def _widen(piece, width: float) -> tuple[object, bool]:
    """Widen the parts of a piece that are thinner than `width`."""
    if width <= 0:
        return piece, False
    opened = piece.buffer(-width / 2, quad_segs=4).buffer(width / 2, quad_segs=4)
    thin = [
        p
        for p in polygons(piece.difference(opened))
        if p.length > 4 * width and stroke_width(p) < 0.9 * width
    ]
    if not thin:
        return piece, False
    grown = [p.buffer((width - stroke_width(p)) / 2, quad_segs=4) for p in thin]
    return clean(shapely.union_all([piece, *grown])), True


def layout(
    drawing: Drawing, params: CoasterParams, overrides: dict[str, Role] | None = None
) -> CoasterLayout:
    warnings: list[str] = []
    ink = clean(drawing.ink)
    if ink.is_empty:
        raise CodedError("nothing_to_make", "Nothing to make a coaster from")
    ink = clean(_normalised(ink).simplify(0.01))
    edge = params.margin + (params.rim_width if params.rim else 0)

    if params.shape == "silhouette":
        longest = params.size - 2 * edge
        if longest < 5:
            raise CodedError("margin_too_big", "The margin leaves no room for the Motif")
        ink = affinity.scale(ink, longest / 100, longest / 100, origin=(0, 0))
        filled = shapely.union_all([Polygon(p.exterior) for p in polygons(ink)])
        plate = clean(_one_piece(filled.buffer(edge, quad_segs=16), warnings))
        inner = clean(plate.buffer(-edge, quad_segs=16))
    else:
        plate = _plate(params)
        inner = clean(plate.buffer(-edge, quad_segs=16))
        if inner.is_empty:
            raise CodedError("margin_too_big", "The margin leaves no room for the Motif")
        scale = _fit(ink, inner) * params.motif_scale
        ink = affinity.scale(ink, scale, scale, origin=(0, 0))

    area = clean(inner.difference(ink)) if params.invert else ink
    pieces, widened, dropped = [], 0, 0
    for piece in _ordered(area):
        piece, grew = _widen(piece, params.min_line)
        widened += grew
        if piece.area < MIN_PIECE:
            dropped += 1
            continue
        pieces.append(clean(piece.intersection(plate.buffer(-0.5))))
    if widened:
        text = f"Widened {widened} Motif line(s) thinner than {params.min_line:g} mm."
        warnings.append(Notice("lines_widened", text, n=widened, mm=params.min_line))
    if dropped:
        text = f"Dropped {dropped} Motif piece(s) smaller than {MIN_PIECE:g} mm²."
        warnings.append(Notice("motif_pieces_dropped", text, n=dropped, mm2=MIN_PIECE))

    features = []
    for i, piece in enumerate(pieces, 1):
        fid = f"m{i}"
        role = (overrides or {}).get(fid, Role.MOTIF)
        if role not in (Role.MOTIF, Role.IGNORE):
            role = Role.MOTIF
        feature = Feature(
            id=fid,
            kind="region",
            role=role,
            default_role=Role.MOTIF,
            path=path_data(piece),
            area=round(piece.area, 2),
        )
        features.append(FeatureShape(feature, piece))

    opener = _opener(plate, params) if params.opener != "none" else None
    feet = _feet(plate, params, warnings) if params.feet else Polygon()
    return CoasterLayout(plate, inner, features, opener, feet, warnings)


def _opener(plate, params: CoasterParams) -> Opener:
    """A tab on one side of the Plate, with an opening the cap goes into.

    The bottle comes from below. The cap's edge hooks under the catch (the
    coin's edge, or the plastic) on the Plate side of the opening; the far end
    of the tab rests on the cap, and lifting the Coaster pries the cap off.
    """
    ux, uy = DIRECTIONS[params.opener_side]
    vx, vy = -uy, ux
    # The Plate's furthest point in that direction, centred along a flat side.
    reach = max(ux * x + uy * y for x, y in plate.exterior.coords)
    angle = math.degrees(math.atan2(uy, ux))
    band = affinity.rotate(box(reach - 0.5, -1e4, reach + 1, 1e4), angle, origin=(0, 0))
    near_band = plate.intersection(band)
    c = near_band.centroid
    across = vx * c.x + vy * c.y

    ax, ay = ux * reach + vx * across, uy * reach + vy * across

    def place(geom):
        # local (s along the direction, t across it) to picture coordinates
        return affinity.affine_transform(geom, [ux, vx, uy, vy, ax, ay])

    def rounded(minx, miny, maxx, maxy, r):
        return box(minx, miny, maxx, maxy).buffer(-r, quad_segs=8).buffer(r, quad_segs=8)

    coin = params.opener == "coin"
    diameter, _ = params.coin_size()
    r = (diameter + COIN_PLAY) / 2
    wall = 2.0
    near = wall + 2 * r - COIN_SHOW if coin else 8.0
    length = CAP_REACH + (COIN_SHOW if coin else 0)
    far = near + length
    width = max(OPENING_WIDTH + 14, 2 * r + 2 * wall + 4)
    tab = rounded(-20, -width / 2, far + 9, width / 2, 14)
    opening = rounded(near, -OPENING_WIDTH / 2, far, OPENING_WIDTH / 2, 10)
    pocket = Point(near + COIN_SHOW - r, 0).buffer(r, quad_segs=32) if coin else Polygon()
    return Opener(place(tab), place(opening), place(pocket))


def _feet(plate, params: CoasterParams, warnings: list[str]):
    """Up to four round recesses, as far out towards the Plate's corners as fit."""
    r = params.foot_diameter / 2
    inset = plate.buffer(-(r + 3))
    if inset.is_empty:
        warnings.append(Notice("feet_no_room", "The Plate is too small for Foot recesses."))
        return Polygon()
    minx, miny, maxx, maxy = plate.bounds
    centres: list[Point] = []
    for corner in ((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)):
        _, p = nearest_points(Point(corner), inset)
        if all(p.distance(q) > 2 * r + 2 for q in centres):
            centres.append(p)
    if len(centres) < 4:
        text = f"Only {len(centres)} Foot recess(es) fit on this Plate."
        warnings.append(Notice("feet_some", text, n=len(centres)))
    return shapely.union_all([p.buffer(r, quad_segs=16) for p in centres])


def build(result: CoasterLayout, params: CoasterParams) -> Coaster:
    warnings = list(result.warnings)
    h, d = params.thickness, params.motif_depth
    style = params.motif_style
    motif = result.motif
    if motif.is_empty:
        warnings.append(
            Notice("no_motif", "No part of the picture is a Motif; the Coaster is a plain Plate.")
        )

    def flip(geom):
        return affinity.scale(geom, 1, -1, origin=(0, 0))

    body, plate = flip(result.body), flip(result.plate)
    motif, feet = flip(motif), flip(result.feet)

    adds = [Layer(body, 0, h)]
    cuts = []
    if style != "raised" and not motif.is_empty:
        if d >= h - 0.6:
            raise CodedError(
                "motif_too_deep",
                f"The Motif depth must be less than {h - 0.6:g} mm on a {h:g} mm Plate",
                max=round(h - 0.6, 2),
                thickness=h,
            )
        cuts.append(Layer(motif, h - d, h))
    if params.rim:
        adds.append(Layer(clean(plate.difference(plate.buffer(-params.rim_width))), h, h + params.rim_height))
    if not feet.is_empty:
        floor = h - (d if style != "raised" else 0)
        if params.foot_depth > floor - 0.6:
            warnings.append(
                Notice("feet_too_deep", "The Foot recesses are too deep for this Plate and were left out.")
            )
        else:
            cuts.append(Layer(feet, 0, params.foot_depth))

    pause_z = None
    if result.opener:
        thick = clean(body.difference(plate.buffer(1e-3)))
        top = max(params.opener_thickness, h)
        adds.append(Layer(thick, h, top))
        pocket = flip(result.opener.pocket)
        if not pocket.is_empty:
            _, coin_t = params.coin_size()
            slot_top = math.ceil(round((COIN_FLOOR + coin_t + 0.2) / LAYER, 6)) * LAYER
            if top < slot_top + 1.0:
                text = f"The opener should be at least {slot_top + 1:g} mm thick to cover the coin."
                warnings.append(Notice("opener_too_thin", text, mm=round(slot_top + 1, 2)))
            cuts.append(Layer(pocket, COIN_FLOOR, slot_top))
            pause_z = round(slot_top + LAYER, 2)

    plate_layers = stack(adds, cuts)
    parts = [Part("plate", plate_layers, extrude(plate_layers), params.plate_colour, 1)]
    if style != "engraved" and not motif.is_empty:
        z0, z1 = (h - d, h) if style == "inlay" else (h, h + d)
        motif_layers = [Layer(motif, z0, z1)]
        parts.append(Part("motif", motif_layers, extrude(motif_layers), params.motif_colour, 2))
    centre([p.mesh for p in parts])

    (x0, y0, z0), (x1, y1, z1) = _bounds([p.mesh for p in parts])
    dims = Dimensions(width=round(x1 - x0, 2), depth=round(y1 - y0, 2), height=round(z1 - z0, 2))
    return Coaster(parts, dims, warnings, pause_z)


def _bounds(meshes):
    lows = [m.bounds[0] for m in meshes]
    highs = [m.bounds[1] for m in meshes]
    return [min(v[i] for v in lows) for i in range(3)], [max(v[i] for v in highs) for i in range(3)]
