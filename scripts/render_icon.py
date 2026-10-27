"""Render the logo and favicons: the gingerbread Cutter, made by Pic2Cookie itself.

    uv run python scripts/render_icon.py

Writes frontend/public/{logo.svg,favicon.svg,favicon-32.png,apple-touch-icon.png,icon-512.png}.
The view is a slightly angled look at the printed Cutter: each layer's walls are
swept upwards in a darker green and capped with a lighter top face.
"""

import math
from pathlib import Path

import shapely
from PIL import Image, ImageDraw
from shapely import affinity
from shapely.geometry import Polygon

from pic2cookie.core.model import CutterParams
from pic2cookie.core.pipeline import make
from pic2cookie.core.roles import polygons

ROOT = Path(__file__).parent.parent
OUT = ROOT / "frontend" / "public"
GREEN, WALL, TOP, EDGE = "#00ae42", "#007a2f", "#3fd27a", "#00561f"
TILT = 0.62  # how much depth is squashed
LIFT = 0.95  # how far height moves things up the screen
TURN = -12  # degrees


def project(geom, z: float):
    turned = affinity.rotate(geom, TURN, origin=(0, 0))
    return affinity.affine_transform(turned, [1, 0, 0, TILT, 0, -z * LIFT])


def swept(region, z0: float, z1: float):
    """The screen area a prism's walls cover between z0 and z1."""
    lo, hi = project(region, z0), project(region, z1)
    parts = [lo, hi]
    for poly in polygons(region):
        for ring in (poly.exterior, *poly.interiors):
            pts = list(ring.coords)
            for a, b in zip(pts, pts[1:], strict=False):
                quad = Polygon(
                    [
                        *project(shapely.LineString([a, b]), z0).coords,
                        *reversed(project(shapely.LineString([a, b]), z1).coords),
                    ]
                )
                if quad.is_valid and quad.area > 0:
                    parts.append(quad)
    return shapely.union_all(parts).buffer(0)


DETAILED = CutterParams(
    size=80, blade_height=13, flange_width=4, blade_thickness=1.6, imprint_thickness=1.4, flange_height=2.5
)
# Favicons are tiny: chunky walls, no imprints.
CHUNKY = CutterParams(
    size=80, blade_height=12, flange_width=5, blade_thickness=5, flange_height=3, min_imprint=50
)


def shapes(params: CutterParams, simplify: float) -> list[tuple[object, str, str]]:
    """(geometry, fill, stroke) in painting order, in screen units."""
    cutter = make((ROOT / "examples" / "gingerbread.svg").read_bytes(), params).cutter
    out = []
    for layer in cutter.layers:
        region = layer.region.simplify(simplify)
        out.append((swept(region, layer.z0, layer.z1), WALL, EDGE))
        out.append((project(region, layer.z1), TOP if layer is not cutter.layers[0] else GREEN, EDGE))
    return out


def fit(items, size: float, pad: float):
    union = shapely.union_all([g for g, _, _ in items])
    minx, miny, maxx, maxy = union.bounds
    scale = (size - 2 * pad) / max(maxx - minx, maxy - miny)
    dx = (size - (maxx - minx) * scale) / 2 - minx * scale
    dy = (size - (maxy - miny) * scale) / 2 - miny * scale
    return [(affinity.affine_transform(g, [scale, 0, 0, scale, dx, dy]), f, s) for g, f, s in items], scale


def path(geom) -> str:
    parts = []
    for poly in polygons(geom):
        for ring in (poly.exterior, *poly.interiors):
            parts.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in list(ring.coords)[:-1]) + "Z")
    return "".join(parts)


def svg(items, size: int, stroke: float) -> str:
    body = "".join(
        f'<path d="{path(g)}" fill="{f}" stroke="{s}" stroke-width="{stroke:g}" '
        'stroke-linejoin="round" fill-rule="evenodd"/>'
        for g, f, s in items
        if not g.is_empty
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">{body}</svg>\n'


def png(items, size: int, stroke: float, background: str | None = None) -> Image.Image:
    k = 4  # supersampling
    image = Image.new("RGBA", (size * k, size * k), background or (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for geom, fill, edge in items:
        for poly in polygons(geom):
            mask = Image.new("L", image.size, 0)
            m = ImageDraw.Draw(mask)
            m.polygon([(x * k, y * k) for x, y in poly.exterior.coords], fill=255)
            for ring in poly.interiors:
                m.polygon([(x * k, y * k) for x, y in ring.coords], fill=0)
            image.paste(Image.new("RGBA", image.size, fill), (0, 0), mask)
            if stroke:
                for ring in (poly.exterior, *poly.interiors):
                    draw.line(
                        [(x * k, y * k) for x, y in ring.coords],
                        fill=edge,
                        width=max(1, math.ceil(stroke * k)),
                        joint="curve",
                    )
    return image.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    detailed, chunky = shapes(DETAILED, 0.15), shapes(CHUNKY, 0.6)
    big, _ = fit(detailed, 512, 24)
    (OUT / "logo.svg").write_text(svg(big, 512, 2.5))
    (OUT / "favicon.svg").write_text(svg(fit(chunky, 64, 1)[0], 64, 0.8))
    png(fit(chunky, 32, 0.5)[0], 32, 0).save(OUT / "favicon-32.png")
    png(fit(detailed, 180, 14)[0], 180, 1.2, background="#ffffff").save(OUT / "apple-touch-icon.png")
    png(big, 512, 2.5).save(OUT / "icon-512.png")
    for name in ("logo.svg", "favicon.svg", "favicon-32.png", "apple-touch-icon.png", "icon-512.png"):
        print(f"{OUT / name}  {(OUT / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
