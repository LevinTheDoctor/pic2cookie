"""Bambu Studio project 3MF: the Product centred on the plate, with printer,
process and filament presets filled in (one AMS slot per coloured part, and a
pause for a Coin insert), so it only needs slicing.

The layout follows what Bambu Studio itself writes (src/libslic3r/Format/bbs_3mf.cpp):
the root model refers to the mesh in 3D/Objects/, and Metadata/ holds the
object/plate settings and the flattened project config.
"""

import json
import uuid
from xml.sax.saxutils import escape, quoteattr

from pic2cookie.core.export import printer, profile
from pic2cookie.core.export.threemf import (
    CONTENT_TYPES,
    CORE_NS,
    mesh_xml,
    package,
    relationships,
)
from pic2cookie.core.model import Material

# Bambu Studio treats a 3MF as its own project when Application starts with this.
APPLICATION = "BambuStudio-02.00.00.00"
BAMBU_NS = "http://schemas.bambulab.com/package/2021"
PROD_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
OBJECT_FILE = "3D/Objects/object_1.model"
IDENTITY = "1 0 0 0 1 0 0 0 1 0 0 0"


def _uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"pic2cookie:{name}"))


def _luminance(colour: str | None) -> float:
    if not colour:
        return 0.5
    r, g, b = (int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _flush(colours: list[str | None]) -> list[str]:
    """Purge volumes (mm³) between filaments: more when going from dark to light."""
    out = []
    for i, a in enumerate(colours):
        for j, b in enumerate(colours):
            out.append("0" if i == j else str(round(150 + 450 * max(0.0, _luminance(b) - _luminance(a)))))
    return out


def project_config(printer_id: str, material: Material, colours: list[str | None] = (None,)) -> dict:
    """Printer, process and filament settings; one filament slot per colour."""
    p = profile(printer_id)
    filament = p["filaments"].get(material.value) or p["filaments"]["pla"]
    n = len(colours)
    config = dict(p["config"])
    config.update({k: v * n if isinstance(v, list) else v for k, v in filament["settings"].items()})
    config.update(
        {
            "printer_settings_id": p["machine"],
            "print_settings_id": p["process"],
            "filament_settings_id": [filament["name"]] * n,
            "filament_ids": [filament["filament_id"]] * n if filament["filament_id"] else [],
            "printer_model": p["printer_model"],
        }
    )
    if any(colours):
        config["filament_colour"] = [(c or "#00AE42").upper() for c in colours]
    if n > 1:
        config["filament_map"] = ["1"] * n
        config["flush_volumes_matrix"] = _flush(list(colours))
        config["flush_volumes_vector"] = ["140"] * (2 * n)
    return config


def _pause(z: float, filaments: int, gcode: str) -> str:
    """Bambu's per-layer custom G-code: type 1 pauses before printing the layer ending at `z`."""
    mode = "MultiExtruder" if filaments > 1 else "SingleExtruder"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<custom_gcodes_per_layer>
<plate>
<plate_info id="1"/>
<layer top_z="{z:g}" type="1" extruder="1" color="" extra="Insert the coin" gcode={quoteattr(gcode)}/>
<mode value="{mode}"/>
</plate>
</custom_gcodes_per_layer>
"""


def to_bambu_3mf(
    parts, name: str, printer_id: str, material: Material, pause_z: float | None = None
) -> bytes:
    bed = printer(printer_id).bed
    placed = f"1 0 0 0 1 0 0 0 1 {bed[0] / 2:g} {bed[1] / 2:g} 0"
    root_id = len(parts) + 1
    head = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
        f'xmlns="{CORE_NS}" xmlns:BambuStudio="{BAMBU_NS}" xmlns:p="{PROD_NS}" '
        'requiredextensions="p">\n'
    )
    components = "".join(
        f'<component p:path="/{OBJECT_FILE}" objectid="{i + 1}" '
        f'p:UUID="{_uuid(f"component{i}")}" transform="{IDENTITY}"/>'
        for i in range(len(parts))
    )
    root = (
        head
        + f' <metadata name="Application">{APPLICATION}</metadata>\n'
        + ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        + f' <metadata name="Title">{escape(name)}</metadata>\n'
        + " <resources>\n"
        + f'  <object id="{root_id}" p:UUID="{_uuid("object")}" type="model">\n'
        + f"   <components>{components}</components>\n"
        + "  </object>\n </resources>\n"
        + f' <build p:UUID="{_uuid("build")}">\n'
        + f'  <item objectid="{root_id}" p:UUID="{_uuid("item")}" transform="{placed}" printable="1"/>\n'
        + " </build>\n</model>\n"
    )
    meshes = "".join(
        f'  <object id="{i + 1}" p:UUID="{_uuid(f"mesh{i}")}" type="model">{mesh_xml(part.mesh)}</object>\n'
        for i, part in enumerate(parts)
    )
    obj = (
        head
        + f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n{meshes} </resources>\n <build/>\n</model>\n'
    )
    n = quoteattr(name)
    part_settings = "".join(
        f"""    <part id="{i + 1}" subtype="normal_part">
      <metadata key="name" value={quoteattr(part.name if len(parts) > 1 else name)}/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="{i}"/>
      <metadata key="extruder" value="{part.filament}"/>
      <mesh_stat face_count="{len(part.mesh.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
"""
        for i, part in enumerate(parts)
    )
    faces = sum(len(part.mesh.faces) for part in parts)
    settings = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="{root_id}">
    <metadata key="name" value={n}/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{faces}"/>
{part_settings}  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <model_instance>
      <metadata key="object_id" value="{root_id}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="1"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="{root_id}" instance_id="0" transform="{placed}" offset="0 0 0" />
  </assemble>
</config>
"""
    slots = max(part.filament for part in parts)
    colours = [next((p.colour for p in parts if p.filament == slot), None) for slot in range(1, slots + 1)]
    files = {
        "[Content_Types].xml": CONTENT_TYPES,
        "_rels/.rels": relationships("/3D/3dmodel.model"),
        "3D/3dmodel.model": root,
        "3D/_rels/3dmodel.model.rels": relationships(f"/{OBJECT_FILE}"),
        OBJECT_FILE: obj,
        "Metadata/model_settings.config": settings,
        "Metadata/project_settings.config": json.dumps(
            project_config(printer_id, material, colours), indent=4
        ),
    }
    if pause_z is not None:
        pause = profile(printer_id)["config"].get("machine_pause_gcode", "M400 U1")
        files["Metadata/custom_gcode_per_layer.xml"] = _pause(pause_z, slots, pause)
    return package(files)
