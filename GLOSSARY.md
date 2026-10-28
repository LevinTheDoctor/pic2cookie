# Pic2Cookie

Turns a picture (SVG, or a raster image traced to SVG) into a 3D-printable cookie cutter or coaster.

## Language

The page is in English and German; each term's _German_ name is what the German page says.

**Product**:
What a Design is turned into: a Cutter or a Coaster. A Design makes one Product at a time and can be switched to the other.
_German_: Produkt
_Avoid_: type, mode, object

### The cutter

**Cutter**:
The Product that cuts dough: blades standing on a flange, printed flange-down.
_German_: Ausstecher
_Avoid_: model, mesh, stamp

**Blade**:
A thin, full-height wall that cuts through the dough.
_German_: Klinge
_Avoid_: wall, edge

**Outer blade**:
The Blade that follows the outer boundary of the Silhouette.
_German_: Außenklinge

**Inner blade**:
A Blade that follows the boundary of a Hole, so the cookie gets a cut-out there.
_German_: Innenklinge
_Avoid_: inside blade

**Flange**:
The flat rim along the base of the Outer blade that you press on and that stiffens the blade.
_German_: Flansch
_Avoid_: brim, lip, rim, base

**Imprint blade**:
A shorter blade inside the Silhouette that marks the dough without cutting through it, such as sprinkles or the edge of a glazing.
_German_: Prägeklinge
_Avoid_: short blade, detail, stamp, embosser

**Bridge**:
A thin bar at Flange height that connects an Imprint blade to the nearest Blade so it is held in place.
_German_: Steg
_Avoid_: strut, connector

**Back plate**:
A solid plate at Flange height covering the inside of the Cutter, holding Imprint blades instead of Bridges.
_German_: Rückplatte
_Avoid_: lid, cover

**Filament estimate**:
The expected filament use of a Cutter (grams, metres and cost), derived from its volume and the Material; a slicer may differ.
_German_: Filamentbedarf
_Avoid_: filament usage, consumption

**Material**:
The filament type chosen for printing (PLA, PETG, ABS), which fixes the density used for the Filament estimate.
_German_: Material

### The coaster

**Coaster**:
The Product you put a glass on: a flat Plate carrying the Motif on top, optionally with a Rim and a Bottle opener.
_German_: Untersetzer

**Plate**:
The flat body of a Coaster, in one of the Plate shapes.
_German_: Platte
_Avoid_: base, body

**Plate shape**:
The outline of the Plate: round, square, rounded square, or Silhouette (the picture's own outline plus a margin).
_German_: Form

**Motif**:
The picture as it appears on the top of a Coaster, centred and kept inside the Plate.
_German_: Motiv
_Avoid_: imprint (that is the Cutter's Imprint blade), logo, decal

**Motif style**:
How the Motif sits on the Plate: Inlay (a second colour, flush with the top), Raised (standing up from the top) or Engraved (cut into the top).
_German_: Eingelegt / Erhaben / Graviert

**Rim**:
A low lip along the edge of a Coaster's top that keeps drips on the Coaster.
_German_: Randleiste
_Avoid_: border, edge, Flange (that is the Cutter's)

**Bottle opener**:
An optional tab sticking out from the Plate, with an opening that catches a bottle cap on the edge of a Coin insert.
_German_: Flaschenöffner
_Avoid_: opener hook

**Coin insert**:
A coin placed into a slot in the Bottle opener while it is printed, sealed in by the layers above; its edge lifts the cap.
_German_: Münzeinsatz

**Foot recess**:
One of four shallow pockets on a Coaster's underside for stick-on rubber or felt pads.
_German_: Mulde für Füße
_Avoid_: foot, pad

### The picture

**Silhouette**:
The cookie's shape: everything the Ink covers, merged into one area.
_German_: Silhouette
_Avoid_: outline, shape, contour

**Hole**:
An area inside the Silhouette, large enough to matter, that is cut out of the cookie.
_German_: Loch

**Ink**:
The colour in the source picture that counts as drawing (black by default); everything else is background.
_German_: Zeichenfarbe
_Avoid_: foreground, mask

**Role**:
What a line or region of the picture becomes in the Product. In a Cutter: Outer blade, Hole, Imprint blade, or Ignore. In a Coaster: Motif or Ignore. Assigned automatically and changeable by the user.
_German_: Rolle

**Design**:
A saved unit of work: the source picture, its traced SVG, the chosen Product and parameters, and the generated files.
_German_: Entwurf
_Avoid_: project, job
