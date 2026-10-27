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


def to_3mf(mesh, name: str) -> bytes:
    """A plain 3MF that any slicer can open."""
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<model unit="millimeter" xml:lang="en-US" xmlns="{CORE_NS}">\n'
        f' <metadata name="Title">{escape(name)}</metadata>\n'
        f' <metadata name="Application">Pic2Cookie</metadata>\n'
        f' <resources><object id="1" name="{escape(name, {chr(34): "&quot;"})}" type="model">'
        f"{mesh_xml(mesh)}</object></resources>\n"
        ' <build><item objectid="1"/></build>\n'
        "</model>\n"
    )
    return package(
        {
            "[Content_Types].xml": CONTENT_TYPES,
            "_rels/.rels": relationships("/3D/3dmodel.model"),
            "3D/3dmodel.model": model,
        }
    )
