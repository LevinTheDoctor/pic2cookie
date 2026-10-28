import io
import json
import zipfile
from xml.etree import ElementTree as ET

import pytest
import trimesh

from pic2cookie.core.export import Format, bed_warning, export
from pic2cookie.core.model import CoasterParams, Dimensions, Product, Role
from pic2cookie.core.pipeline import make_coaster


def coaster(data: bytes, **params):
    return make_coaster(data, CoasterParams(**params))


def parts(result) -> dict:
    return {p.name: p for p in result.coaster.parts}


def assert_printable(result):
    for part in result.coaster.parts:
        assert part.mesh.is_watertight, part.name
        assert part.mesh.volume == pytest.approx(part.volume_mm3, rel=0.01)


@pytest.mark.parametrize("shape", ["round", "square", "rounded", "silhouette"])
def test_shapes(fixture_bytes, shape):
    result = coaster(fixture_bytes("donut_filled.svg"), shape=shape)
    assert_printable(result)
    d = result.coaster.dimensions
    assert max(d.width, d.depth) == pytest.approx(100, abs=0.5)
    assert d.height == 4
    assert set(parts(result)) == {"plate", "motif"}


def test_round_coaster_is_a_disc(fixture_bytes):
    plate = parts(coaster(fixture_bytes("hi.svg")))["plate"]
    assert plate.layers[0].region.area == pytest.approx(3.1416 * 50**2, rel=0.01)


def test_motif_fits_inside_the_margin(fixture_bytes):
    result = coaster(fixture_bytes("hi.svg"), shape="square", margin=15)
    motif = result.layout.motif
    assert result.layout.plate.buffer(-15 + 0.01).contains(motif)
    minx, miny, maxx, maxy = motif.bounds
    assert max(maxx - minx, maxy - miny) == pytest.approx(70, abs=0.5)  # fills the room left


def test_motif_scale(fixture_bytes):
    full = coaster(fixture_bytes("hi.svg")).layout.motif.area
    half = coaster(fixture_bytes("hi.svg"), motif_scale=0.5).layout.motif.area
    assert half == pytest.approx(full / 4, rel=0.05)


def test_motif_styles(fixture_bytes):
    data = fixture_bytes("hi.svg")
    inlay = parts(coaster(data))
    assert [(layer.z0, layer.z1) for layer in inlay["motif"].layers] == [(3.4, 4.0)]
    # the inlay sits in a pocket of the Plate: together they are a solid 4 mm disc
    total = inlay["plate"].volume_mm3 + inlay["motif"].volume_mm3
    assert total == pytest.approx(inlay["plate"].layers[0].region.area * 4, rel=0.001)

    raised = parts(coaster(data, motif_style="raised"))
    assert [(layer.z0, layer.z1) for layer in raised["motif"].layers] == [(4.0, 4.6)]

    engraved = coaster(data, motif_style="engraved")
    assert set(parts(engraved)) == {"plate"}
    assert engraved.coaster.volume_mm3 < inlay["plate"].volume_mm3 + 1


def test_text_reads_the_right_way_from_above(fixture_bytes):
    """Coasters are printed face up, so the picture is not mirrored."""
    result = coaster(fixture_bytes("hi.svg"), shape="square")
    motif = parts(result)["motif"].mesh
    h_pieces = [p for p in result.layout.features if p.feature.area > 300]
    assert h_pieces  # the H is the larger letter and is on the left in the picture
    left = motif.vertices[:, 0] < 0
    assert left.sum() > (~left).sum()


def test_roles_toggle_motif_pieces(fixture_bytes):
    data = fixture_bytes("hi.svg")
    result = coaster(data)
    ids = [f.feature.id for f in result.layout.features]
    assert ids == ["m1", "m2"]
    assert all(f.feature.role is Role.MOTIF for f in result.layout.features)
    without = make_coaster(data, CoasterParams(), roles={"m2": Role.IGNORE})
    assert without.layout.motif.area < result.layout.motif.area
    # Cutter roles do not apply to a Coaster
    odd = make_coaster(data, CoasterParams(), roles={"m1": Role.HOLE, "r1": Role.IGNORE})
    assert odd.layout.motif.area == pytest.approx(result.layout.motif.area)


def test_invert(fixture_bytes):
    result = coaster(fixture_bytes("hi.svg"), invert=True)
    inner = result.layout.inner
    assert result.layout.motif.area > 0.5 * inner.area


def test_thin_lines_are_widened(fixture_bytes):
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <rect x="0" y="0" width="100" height="100" fill="none" stroke="black" stroke-width="0.2"/>
      <rect x="40" y="40" width="20" height="20" fill="black"/></svg>"""
    result = coaster(svg, shape="square")
    assert any("Widened" in w for w in result.coaster.warnings)
    assert_printable(result)


def test_rim_and_feet(fixture_bytes):
    result = coaster(fixture_bytes("hi.svg"), rim=True, feet=True)
    assert_printable(result)
    plate = parts(result)["plate"]
    assert result.coaster.dimensions.height == 5.0
    bottom = plate.layers[0]
    assert bottom.z1 == 1.0  # Foot recesses are 1 mm deep
    holes = sum(len(p.interiors) for p in getattr(bottom.region, "geoms", [bottom.region]))
    assert holes == 4


@pytest.mark.parametrize("side", ["right", "left", "top", "bottom"])
def test_bottle_opener_with_coin(fixture_bytes, side):
    result = coaster(fixture_bytes("hi.svg"), opener="coin", opener_side=side)
    assert_printable(result)
    d = result.coaster.dimensions
    assert d.height == 6
    long, short = (d.width, d.depth) if side in ("right", "left") else (d.depth, d.width)
    assert short == pytest.approx(100, abs=0.5)
    assert long > 150  # the tab sticks out
    assert result.coaster.pause_z == 3.8  # first layer above the coin slot
    opener = result.layout.opener
    assert not opener.opening.intersects(result.layout.plate)
    assert opener.pocket.intersection(opener.opening).area > 10  # the coin's edge shows


def test_plastic_opener_has_no_pause(fixture_bytes):
    result = coaster(fixture_bytes("hi.svg"), opener="plastic", shape="silhouette")
    assert_printable(result)
    assert result.coaster.pause_z is None


def test_filament_per_part(fixture_bytes):
    result = make_coaster(fixture_bytes("hi.svg"))
    assert [p.name for p in result.parts] == ["plate", "motif"]
    assert [p.colour for p in result.parts] == ["#ffffff", "#000000"]
    assert sum(p.estimate.grams for p in result.parts) == pytest.approx(result.estimate.grams, abs=0.2)


def test_stl_zip(fixture_bytes):
    result = make_coaster(fixture_bytes("hi.svg"))
    data = export(result.coaster.parts, Format.STL, product=Product.COASTER)
    z = zipfile.ZipFile(io.BytesIO(data))
    assert sorted(z.namelist()) == ["motif.stl", "plate.stl"]
    mesh = trimesh.load(io.BytesIO(z.read("motif.stl")), file_type="stl")
    assert mesh.volume == pytest.approx(result.parts[1].estimate.volume_cm3 * 1000, rel=0.02)
    assert Format.STL.filename(Product.COASTER) == "coaster.stl.zip"


def test_3mf_has_coloured_parts(fixture_bytes):
    result = make_coaster(fixture_bytes("hi.svg"))
    z = zipfile.ZipFile(io.BytesIO(export(result.coaster.parts, Format.THREEMF, name="hi")))
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    model = ET.fromstring(z.read("3D/3dmodel.model"))
    colours = [b.get("displaycolor") for b in model.findall(".//m:base", ns)]
    assert colours == ["#ffffffFF", "#000000FF"]
    assert len(model.findall(".//m:component", ns)) == 2


def test_bambu_project_with_two_filaments_and_a_pause(fixture_bytes):
    result = make_coaster(fixture_bytes("hi.svg"), CoasterParams(opener="coin"))
    data = export(
        result.coaster.parts,
        Format.BAMBU,
        name="hi",
        product=Product.COASTER,
        printer_id="a1mini",
        pause_z=result.coaster.pause_z,
    )
    z = zipfile.ZipFile(io.BytesIO(data))
    config = json.loads(z.read("Metadata/project_settings.config"))
    assert config["filament_colour"] == ["#FFFFFF", "#000000"]
    assert len(config["filament_settings_id"]) == 2
    assert len(config["nozzle_temperature"]) == 2
    assert len(config["flush_volumes_matrix"]) == 4
    settings = ET.fromstring(z.read("Metadata/model_settings.config"))
    extruders = [p.find("metadata[@key='extruder']").get("value") for p in settings.iter("part")]
    assert extruders == ["1", "2"]
    pause = ET.fromstring(z.read("Metadata/custom_gcode_per_layer.xml")).find(".//layer")
    assert pause.get("type") == "1"
    assert float(pause.get("top_z")) == 3.8


def test_bed_warning():
    assert bed_warning(Dimensions(width=170, depth=100, height=6), "a1mini") is None
    assert "does not fit" in bed_warning(Dimensions(width=190, depth=100, height=6), "a1mini")
    assert bed_warning(Dimensions(width=190, depth=100, height=6), "x1c") is None
