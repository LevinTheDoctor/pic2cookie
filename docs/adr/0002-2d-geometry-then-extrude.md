# All geometry in 2D, then extruded

Every boolean step (merging the Silhouette, offsetting Blades, joining Bridges, cutting Holes) happens on 2D polygons with shapely. Each layer of the Cutter is then extruded into a prism with mapbox-earcut and stacked with trimesh. We never use 3D mesh booleans.

## Considered Options

- **3D booleans via trimesh + manifold3d**: more general (it would allow tapered blades), but `manifold3d` has no Python 3.15 wheel (see ADR-0001), and 3D booleans are slower and more fragile than 2D ones.

## Consequences

Cutters are made of straight vertical prisms. Features that change shape with height, such as a tapered cutting edge, would require revisiting this decision.
