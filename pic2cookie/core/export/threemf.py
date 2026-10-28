"""3MF packaging shared by the generic and the Bambu exporter."""

import io
import zipfile
from xml.sax.saxutils import escape

CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
MODEL_TYPE = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
</Types>
"""


def relationships(*targets: str) -> str:
    rels = "".join(
        f' <Relationship Target="{t}" Id="rel-{i + 1}" Type="{MODEL_TYPE}"/>\n' for i, t in enumerate(targets)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        f"{rels}</Relationships>\n"
    )


def mesh_xml(mesh) -> str:
    out = io.StringIO()
    out.write("<mesh><vertices>")
    for x, y, z in mesh.vertices:
        out.write(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>')
    out.write("</vertices><triangles>")
    for a, b, c in mesh.faces:
        out.write(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>')
    out.write("</triangles></mesh>")
    return out.getvalue()


def package(files: dict[str, str | bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def attr(value: str) -> str:
    return escape(value, {'"': "&quot;"})


def to_3mf(parts, name: str) -> bytes:
    """A plain 3MF that any slicer can open; several parts become one object with coloured components."""
    if len(parts) == 1:
        resources = f'<object id="1" name="{attr(name)}" type="model">{mesh_xml(parts[0].mesh)}</object>'
        item = 1
    else:
        bases = "".join(
            f'<base name="{attr(p.name)}" displaycolor="{p.colour or "#808080"}FF"/>' for p in parts
        )
        objects = "".join(
            f'<object id="{i + 2}" name="{attr(p.name)}" type="model" pid="1" pindex="{i}">'
            f"{mesh_xml(p.mesh)}</object>"
            for i, p in enumerate(parts)
        )
        item = len(parts) + 2
        components = "".join(f'<component objectid="{i + 2}"/>' for i in range(len(parts)))
        resources = (
            f'<basematerials id="1">{bases}</basematerials>{objects}'
            f'<object id="{item}" name="{attr(name)}" type="model">'
            f"<components>{components}</components></object>"
        )
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<model unit="millimeter" xml:lang="en-US" xmlns="{CORE_NS}">\n'
        f' <metadata name="Title">{escape(name)}</metadata>\n'
        f' <metadata name="Application">Pic2Cookie</metadata>\n'
        f" <resources>{resources}</resources>\n"
        f' <build><item objectid="{item}"/></build>\n'
        "</model>\n"
    )
    return package(
        {
            "[Content_Types].xml": CONTENT_TYPES,
            "_rels/.rels": relationships("/3D/3dmodel.model"),
            "3D/3dmodel.model": model,
        }
    )
