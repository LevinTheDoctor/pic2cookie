import io
import json
import zipfile
from xml.etree import ElementTree as ET

import pytest
import trimesh

from pic2cookie.core import filament
from pic2cookie.core.export import Format, export, printers
from pic2cookie.core.model import CutterParams, FilamentParams, Material, Role, TraceParams
from pic2cookie.core.outline import SvgError, parse_svg
from pic2cookie.core.pipeline import make
from pic2cookie.core.trace import TraceError, trace


def assert_printable(result, params: CutterParams):
    mesh = result.cutter.mesh
    shells = mesh.split(only_watertight=False)
    assert shells and all(s.is_watertight for s in shells)
    assert mesh.bounds[0][2] == pytest.approx(0)
    assert mesh.bounds[1][2] == pytest.approx(params.blade_height)
    # Layers do not overlap, so the mesh volume matches the layered volume.
    assert mesh.volume == pytest.approx(result.cutter.volume_mm3, rel=0.01)
    silhouette = result.layout.silhouette
    minx, miny, maxx, maxy = silhouette.bounds
    assert max(maxx - minx, maxy - miny) == pytest.approx(params.size, rel=1e-3)


def roles(result):
    return {f.feature.id: f.feature.role for f in result.layout.features}


def test_filled_donut_has_hole_and_imprints(fixture_bytes):
    result = make(fixture_bytes("donut_filled.svg"))
    assert result.layout.style == "filled"
    found = roles(result)
    assert list(found.values()).count(Role.HOLE) == 1
    assert list(found.values()).count(Role.IMPRINT) >= 3  # glaze edge and sprinkles
    assert_printable(result, CutterParams())
    # Three heights: Flange, Imprint blades, full Blades.
    assert [layer.z1 for layer in result.cutter.layers] == [2.0, 12.0, 15.0]


def test_bridges_join_everything_into_one_base(fixture_bytes):
    result = make(fixture_bytes("donut_filled.svg"))
    base = result.cutter.layers[0].region
    assert base.geom_type == "Polygon"


def test_back_plate_covers_the_cookie(fixture_bytes):
    bridges = make(fixture_bytes("donut_filled.svg"))
    plate = make(fixture_bytes("donut_filled.svg"), CutterParams(support="plate"))
    assert plate.cutter.layers[0].region.area > 2 * bridges.cutter.layers[0].region.area
    assert_printable(plate, CutterParams())


def test_line_donut_defaults_and_hole_override(fixture_bytes):
    result = make(fixture_bytes("donut_lines.svg"))
    assert result.layout.style == "line"
    found = roles(result)
    assert Role.HOLE not in found.values()
    assert sum(1 for fid, r in found.items() if fid.startswith("l") and r is Role.IMPRINT) >= 3

    # The smallest enclosed region is inside the hole circle; marking it cuts it out.
    regions = [f.feature for f in result.layout.features if f.feature.kind == "region"]
    inner = min(regions, key=lambda f: f.area)
    marked = make(fixture_bytes("donut_lines.svg"), roles={inner.id: Role.HOLE})
    assert roles(marked)[inner.id] is Role.HOLE
    assert marked.cutter.volume_mm3 > result.cutter.volume_mm3
    assert_printable(marked, CutterParams())


def test_separate_shapes_keep_the_largest(fixture_bytes):
    result = make(fixture_bytes("hi.svg"))
    assert any("separate shapes" in w for w in result.cutter.warnings)
    assert_printable(result, CutterParams())


def test_thin_tail_still_printable(fixture_bytes):
    params = CutterParams(size=60, blade_height=12)
    assert_printable(make(fixture_bytes("cat.svg"), params), params)


def test_small_holes_are_dropped(fixture_bytes):
    result = make(fixture_bytes("donut_filled.svg"), CutterParams(size=20))
    assert Role.HOLE not in roles(result).values()
    assert any("hole" in w.lower() for w in result.cutter.warnings)


def test_marked_svg_round_trip(fixture_bytes):
    first = make(fixture_bytes("donut_lines.svg"), roles={"r3": Role.HOLE})
    again = make(first.marked_svg.encode())
    assert again.layout.style == "marked"
    assert roles(again) == roles(first)
    assert again.cutter.volume_mm3 == pytest.approx(first.cutter.volume_mm3, rel=0.01)


def test_svg_errors():
    with pytest.raises(SvgError):
        parse_svg(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>")
    with pytest.raises(SvgError):
        parse_svg(b"<html></html>")


def test_white_shapes_cut_ink():
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <rect width="100" height="100" fill="white"/>
      <circle cx="50" cy="50" r="40"/>
      <circle cx="50" cy="50" r="20" style="fill:#ffffff"/></svg>"""
    drawing = parse_svg(svg)
    assert drawing.ink.area == pytest.approx(3.14159 * (40**2 - 20**2), rel=0.01)


def test_trace_png_donut(donut_png):
    result = make(donut_png)
    assert result.layout.style == "filled"
    assert list(roles(result).values()).count(Role.HOLE) == 1
    assert_printable(result, CutterParams())


def test_trace_picks_ink_colour(red_star_png):
    svg = trace(red_star_png, TraceParams(ink="#dc1e1e"))
    drawing = parse_svg(svg)
    minx, miny, maxx, maxy = drawing.ink.bounds
    assert minx > 10 and miny > 10  # the blue square is not Ink
    alpha = parse_svg(trace(red_star_png, TraceParams(ink="alpha")))
    assert alpha.ink.area > drawing.ink.area


def test_trace_rejects_non_images():
    with pytest.raises(TraceError):
        trace(b"not an image")


def test_filament_estimate():
    est = filament.estimate(10_000, FilamentParams(material=Material.PLA, price_per_kg=20))
    assert est.grams == pytest.approx(12.4)
    assert est.metres == pytest.approx(4.16, abs=0.01)
    assert est.cost == pytest.approx(0.25)
    assert filament.estimate(10_000, FilamentParams(material=Material.ABS)).grams < est.grams


@pytest.fixture(scope="module")
def donut_cutter():
    from pathlib import Path

    return make((Path(__file__).parent / "fixtures/donut_filled.svg").read_bytes()).cutter


def test_stl_export(donut_cutter):
    mesh = trimesh.load(io.BytesIO(export(donut_cutter.mesh, Format.STL)), file_type="stl")
    assert mesh.volume == pytest.approx(donut_cutter.mesh.volume, rel=1e-3)


def test_3mf_export(donut_cutter):
    z = zipfile.ZipFile(io.BytesIO(export(donut_cutter.mesh, Format.THREEMF, name="a & b")))
    model = ET.fromstring(z.read("3D/3dmodel.model"))
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    assert len(model.findall(".//m:triangle", ns)) == len(donut_cutter.mesh.faces)


@pytest.mark.parametrize("printer", [p.id for p in printers()])
def test_bambu_export(donut_cutter, printer):
    data = export(donut_cutter.mesh, Format.BAMBU, name="<donut>", printer_id=printer, material=Material.PETG)
    z = zipfile.ZipFile(io.BytesIO(data))
    for name in z.namelist():
        if name.endswith("project_settings.config"):
            config = json.loads(z.read(name))
        else:
            ET.fromstring(z.read(name))
    assert config["printer_model"].startswith("Bambu Lab")
    assert config["filament_type"] == ["PETG"]
    root = z.read("3D/3dmodel.model").decode()
    assert "BambuStudio-" in root
    bed = next(p for p in printers() if p.id == printer).bed
    assert f"{bed[0] / 2:g} {bed[1] / 2:g} 0" in root
