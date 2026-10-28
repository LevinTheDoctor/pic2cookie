"""2D regions over z ranges in, closed meshes out (ADR-0002)."""

from dataclasses import dataclass

lazy import shapely
lazy import trimesh

from pic2cookie.core.roles import clean, polygons


@dataclass
class Layer:
    region: object  # (Multi)Polygon
    z0: float
    z1: float


@dataclass
class Part:
    """One printed body of a Product, in its own colour and filament slot."""

    name: str
    layers: list[Layer]
    mesh: object  # trimesh.Trimesh
    colour: str | None = None
    filament: int = 1

    @property
    def volume_mm3(self) -> float:
        return volume(self.layers)


def stack(adds: list[Layer], cuts: list[Layer] = ()) -> list[Layer]:
    """Non-overlapping Layers covering `adds` minus `cuts`, split wherever any of them starts or ends."""
    zs = sorted({z for layer in (*adds, *cuts) for z in (layer.z0, layer.z1)})
    out = []
    for z0, z1 in zip(zs, zs[1:], strict=False):
        mid = (z0 + z1) / 2
        region = shapely.union_all(_covering(adds, mid) or [shapely.Polygon()])
        if cut := _covering(cuts, mid):
            region = region.difference(shapely.union_all(cut))
        region = clean(region)
        if region.is_empty:
            continue
        if out and out[-1].z1 == z0 and out[-1].region.equals(region):
            out[-1].z1 = z1
        else:
            out.append(Layer(region, z0, z1))
    return out


def _covering(layers: list[Layer], z: float) -> list:
    return [layer.region for layer in layers if layer.z0 <= z <= layer.z1]


def extrude(layers: list[Layer]):
    """One mesh of stacked prisms; each prism is a closed shell."""
    meshes = []
    for layer in layers:
        # Shrinking by a micron splits rings that touch at a point, which would
        # otherwise share a vertical edge between four faces.
        for poly in polygons(layer.region.buffer(-1e-3, join_style="mitre")):
            mesh = trimesh.creation.extrude_polygon(poly, layer.z1 - layer.z0, engine="earcut")
            mesh.apply_translation((0, 0, layer.z0))
            meshes.append(mesh)
    return trimesh.util.concatenate(meshes)


def centre(meshes: list) -> None:
    """Move meshes together so they are centred on x/y and stand on z=0."""
    lo, hi = trimesh.util.concatenate(meshes).bounds
    offset = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])
    for mesh in meshes:
        mesh.apply_translation(offset)


def volume(layers: list[Layer]) -> float:
    return sum(layer.region.area * (layer.z1 - layer.z0) for layer in layers)
