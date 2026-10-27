"""Bambu Studio project 3MF: the Cutter centred on the plate, with printer,
process and filament presets filled in, so it only needs slicing.

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


def project_config(printer_id: str, material: Material) -> dict:
    p = profile(printer_id)
    filament = p["filaments"].get(material.value) or p["filaments"]["pla"]
    config = dict(p["config"])
    config.update(filament["settings"])
    config.update(
        {
            "printer_settings_id": p["machine"],
            "print_settings_id": p["process"],
            "filament_settings_id": [filament["name"]],
            "filament_ids": [filament["filament_id"]] if filament["filament_id"] else [],
            "printer_model": p["printer_model"],
        }
    )
    return config


def to_bambu_3mf(mesh, name: str, printer_id: str, material: Material) -> bytes:
    bed = printer(printer_id).bed
    placed = f"1 0 0 0 1 0 0 0 1 {bed[0] / 2:g} {bed[1] / 2:g} 0"
    head = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
        f'xmlns="{CORE_NS}" xmlns:BambuStudio="{BAMBU_NS}" xmlns:p="{PROD_NS}" '
        'requiredextensions="p">\n'
    )
    root = (
        head
        + f' <metadata name="Application">{APPLICATION}</metadata>\n'
        + ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        + f' <metadata name="Title">{escape(name)}</metadata>\n'
        + " <resources>\n"
        + f'  <object id="2" p:UUID="{_uuid("object")}" type="model">\n'
        + f'   <components><component p:path="/{OBJECT_FILE}" objectid="1" '
        + f'p:UUID="{_uuid("component")}" transform="{IDENTITY}"/></components>\n'
        + "  </object>\n </resources>\n"
        + f' <build p:UUID="{_uuid("build")}">\n'
        + f'  <item objectid="2" p:UUID="{_uuid("item")}" transform="{placed}" printable="1"/>\n'
        + " </build>\n</model>\n"
    )
    obj = (
        head + f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
        f'  <object id="1" p:UUID="{_uuid("mesh")}" type="model">{mesh_xml(mesh)}</object>\n'
        " </resources>\n <build/>\n</model>\n"
    )
    n = quoteattr(name)
    settings = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value={n}/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{len(mesh.faces)}"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value={n}/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <mesh_stat face_count="{len(mesh.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <model_instance>
      <metadata key="object_id" value="2"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="1"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="2" instance_id="0" transform="{placed}" offset="0 0 0" />
  </assemble>
</config>
"""
    return package(
        {
            "[Content_Types].xml": CONTENT_TYPES,
            "_rels/.rels": relationships("/3D/3dmodel.model"),
            "3D/3dmodel.model": root,
            "3D/_rels/3dmodel.model.rels": relationships(f"/{OBJECT_FILE}"),
            OBJECT_FILE: obj,
            "Metadata/model_settings.config": settings,
            "Metadata/project_settings.config": json.dumps(project_config(printer_id, material), indent=4),
        }
    )
