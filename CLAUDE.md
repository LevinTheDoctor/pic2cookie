# Pic2Cookie

Picture (SVG/PNG/JPG/WebP) in, 3D-printable cookie cutter out. Python 3.15 + uv backend (`pic2cookie/`), React + Vite + TS frontend (`frontend/`), Helm chart (`charts/pic2cookie`). Read `GLOSSARY.md` before naming things; decisions are in `docs/adr/`.

## Layout

- `pic2cookie/core/`: pure logic. `outline` (SVG to Ink), `trace` (raster to SVG), `roles` (Silhouette, features, Roles), `cutter` (layered 2D regions to mesh), `filament`, `export/` (STL, 3MF, Bambu project), `pipeline.make` ties them together.
- `pic2cookie/service.py`: Design operations shared by API, CLI and worker. `storage.py` (fs/S3 blobs, design.json/MongoDB records), `jobs.py` (inline/RQ), `settings.py` (`PIC2COOKIE_*` env).
- `pic2cookie/api.py` (FastAPI, also serves `frontend/dist`) and `pic2cookie/cli.py` (Typer).

## Conventions

- Heavy third-party modules are imported with `lazy import` (ADR-0001); keep `pic2cookie --help` fast.
- Geometry is 2D shapely, then extruded; no 3D booleans (ADR-0002).
- Docker is only built in GitHub Actions, never locally.

## Commands

- `uv run pytest`, `uv run ruff check . && uv run ruff format --check .`
- `cd frontend && npm run lint && npm test && npm run build`
- `scripts/start.sh [--dev]`, `helm lint charts/pic2cookie`

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
