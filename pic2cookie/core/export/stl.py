"""Binary STL, or a zip with one STL per part."""

import io
import zipfile

lazy import trimesh


def to_stl(mesh) -> bytes:
    return trimesh.exchange.stl.export_stl(mesh)


def to_stl_zip(parts) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for part in parts:
            z.writestr(f"{part.name}.stl", to_stl(part.mesh))
    return buf.getvalue()
