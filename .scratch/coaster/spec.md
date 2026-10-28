# Spec: Coasters

Status: done

A Design can make a second **Product**, a **Coaster**: a flat **Plate** with the picture as its **Motif** on top. Vocabulary: `GLOSSARY.md`.

## Product
- Chosen at upload (Cutter by default) and switchable on the Design; one Product at a time. Both keep their own settings; Duplicate gives you both.
- Roles in a Coaster: each Ink piece (`m1`, `m2`, …) is Motif (default) or Ignore. Cutter roles (`r*`, `l*`) are kept but not used.

## Plate
- Plate shapes: round, square, rounded square (10 mm corners), Silhouette (the picture's outline plus the margin). Separate picture parts are joined for the Silhouette shape.
- Defaults: 100 mm diameter/side (for Silhouette: longest side), 4 mm thick.
- Optional Rim (3 mm wide, 1 mm high), off by default.
- Optional Foot recesses: four 10 mm × 1 mm pockets underneath, as far out towards the corners as fit; off by default.

## Motif
- The Ink, centred and scaled to the largest size that fits inside the margin (10 mm, plus the Rim); `motif_scale` makes it smaller, never larger. Invert makes the background the Motif.
- Motif styles: Inlay (default, flush, 0.6 mm deep, second colour), Raised (0.6 mm, second colour), Engraved (0.6 mm, one colour).
- Lines thinner than 0.5 mm are widened, pieces under 1 mm² dropped, both with a warning.
- Printed face up, not mirrored.

## Bottle opener
- Optional, off by default: a tab on the left/right/top/bottom of the Plate (at its furthest point that way), with an opening for the cap (34 mm wide, 24 mm from the catch to the far end).
- Coin insert (default 2 €; 1 €, 50 ct, US quarter or a custom size): a slot 1.2 mm above the bed; the coin's edge reaches 3 mm into the opening and catches the cap. The tab is 6 mm thick; the Bambu project pauses before the first layer above the slot. Plastic-only opener without a coin as a fallback.
- The tab comes on top of the size; a warning when the Coaster does not fit the printer's bed.

## Output
- STL: a zip with `plate.stl` and `motif.stl`. 3MF: one object with two coloured parts. Bambu project: AMS slot 1 = Plate (white), slot 2 = Motif (black), flush volumes, and the coin pause (`Metadata/custom_gcode_per_layer.xml`, type 1).
- Filament estimate per colour plus the total.
- CLI: `make --product coaster --shape … --motif-style … --opener …`.

## Not verified
- Opening the Bambu project in Bambu Studio and a real print (fit of the coin, how well the opener works).
