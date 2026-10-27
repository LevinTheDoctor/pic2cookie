# Spec: Pic2Cookie v1

Status: ready-for-agent

Turn a picture (SVG, or PNG/JPG/WebP traced to SVG) into a printable **Cutter**, with a **Filament estimate**, via CLI, FastAPI and a React frontend. Vocabulary: `GLOSSARY.md`. Decisions: `docs/adr/`.

## Geometry
- Cutter = Blades on a Flange, printed flange-down. Outer blade along the Silhouette, Inner blade per Hole, Imprint blades `imprint_offset` (3 mm) shorter, held by Bridges (default) or a Back plate.
- Defaults: longest side 80 mm, blade 15 x 0.8 mm, flange 4 mm wide x 2 mm, bridge 3 mm wide.
- Always rescaled to the longest side; the SVG's own units are ignored.
- Holes narrower than `min_hole` (8 mm) and Imprint pieces smaller than `min_imprint` (2 mm) are dropped with a warning; narrow parts that turn solid give a warning.
- Several separate shapes: keep the largest, warn.
- Print orientation is mirrored so that the cookie matches the picture when the cutter is flipped for use.
- 2D booleans in shapely, then layered prisms (ADR-0002). Every shell is watertight; layers do not overlap.

## Roles
- Filled drawings (Ink covers >= 50 % of the Silhouette): enclosed background areas become Holes; small ones become Imprint blades.
- Line drawings: the outermost line becomes the Outer blade; inner lines become Imprint blades; enclosed areas are dough (Ignore).
- Every feature has a stable id; per-id Role overrides are stored with the Design. A role-marked SVG (`data-role` per element) is exported and accepted by the CLI.

## Input
- Raster: pick the Ink colour (default black) with tolerance, or `alpha`; invert; OpenCV contours; simplified; emitted as SVG.
- SVG: painter's order; non-background fills/strokes are Ink, white ones subtract.

## Output
- Binary STL, generic 3MF, Bambu project 3MF (printer presets: A1 mini (default), A1, P1S, P2S, X1C, H2D; model centred on the plate).
- "Open in Bambu Studio" link: `bambustudio://open?file=<url>`.
- Filament estimate: grams, metres (1.75 mm), cost; PLA 1.24 / PETG 1.27 / ABS 1.04 g/cm3.

## App
- Python 3.15, `lazy import` (ADR-0001), uv. Package `pic2cookie/`.
- CLI: `make`, `trace`, `serve`, `worker`, `designs ls|show|rm|export`.
- API is job-shaped; executor `inline` (thread pool) or `rq` (Redis).
- Blob storage `fs` | `s3`; Design records as `design.json` in the blob store, or MongoDB when `PIC2COOKIE_DATABASE__URI` is set (ADR-0003).
- Designs keep only their latest version; Duplicate; manual delete; optional `retention.days`.
- Settings: `PIC2COOKIE_*` env vars / `.env`, nested with `__`. No login.

## Frontend
React + Vite + TypeScript, Heroicons, Bambu-green palette, light/dark from the system. Upload, 2D role view (click to switch), three.js preview, Filament estimate, downloads, saved Designs. Static gingerbread-cutter favicon + logo.

## Ops
Private repo `LevinTheDoctor/pic2cookie`. One multi-arch image (amd64/arm64) and an OCI Helm chart on GHCR. GitHub Actions: lint/test on PRs, build/push on `main` and tags. docker compose (mongo by default; `redis`, `minio` profiles). Helm: optional single-node MongoDB pinned to amd64; worker as sidecar when `fs` + `rq`. `scripts/start.sh [--dev]`. Docker is not run locally.

## Tests
pytest on core with fixtures (donut with hole/imprints/sprinkles, "HI", cat with thin tail): watertight shells, size, volume. API tests via TestClient. Vitest smoke test.
