# Pic2Cookie

Turns a picture (SVG, or a raster image traced to SVG) into a 3D-printable cookie cutter.

## Language

### The cutter

**Cutter**:
The single printable object produced from a Design: blades standing on a flange, printed flange-down.
_Avoid_: model, mesh, stamp

**Blade**:
A thin, full-height wall that cuts through the dough.
_Avoid_: wall, edge

**Outer blade**:
The Blade that follows the outer boundary of the Silhouette.

**Inner blade**:
A Blade that follows the boundary of a Hole, so the cookie gets a cut-out there.
_Avoid_: inside blade

**Flange**:
The flat rim along the base of the Outer blade that you press on and that stiffens the blade.
_Avoid_: brim, lip, rim, base

**Imprint blade**:
A shorter blade inside the Silhouette that marks the dough without cutting through it, such as sprinkles or the edge of a glazing.
_Avoid_: short blade, detail, stamp, embosser

**Bridge**:
A thin bar at Flange height that connects an Imprint blade to the nearest Blade so it is held in place.
_Avoid_: strut, connector

**Back plate**:
A solid plate at Flange height covering the inside of the Cutter, holding Imprint blades instead of Bridges.
_Avoid_: lid, cover

**Filament estimate**:
The expected filament use of a Cutter (grams, metres and cost), derived from its volume and the Material; a slicer may differ.
_Avoid_: filament usage, consumption

**Material**:
The filament type chosen for printing (PLA, PETG, ABS), which fixes the density used for the Filament estimate.

### The picture

**Silhouette**:
The cookie's shape: everything the Ink covers, merged into one area.
_Avoid_: outline, shape, contour

**Hole**:
An area inside the Silhouette, large enough to matter, that is cut out of the cookie.

**Ink**:
The colour in the source picture that counts as drawing (black by default); everything else is background.
_Avoid_: foreground, mask

**Role**:
What a line or region of the picture becomes in the Cutter: Outer blade, Hole, Imprint blade, or Ignore. Assigned automatically and changeable by the user.

**Design**:
A saved unit of work: the source picture, its traced SVG, the chosen parameters, and the generated files.
_Avoid_: project, job
