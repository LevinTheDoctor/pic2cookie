"""Binary STL."""

lazy import trimesh


def to_stl(mesh) -> bytes:
    return trimesh.exchange.stl.export_stl(mesh)
