# Pic2Cookie

Picture (SVG/PNG/JPG/WebP) in, 3D-printable cookie cutter or coaster (the two Products) out. Python 3.15 + uv backend (`pic2cookie/`), React + Vite + TS frontend (`frontend/`), Helm chart (`charts/pic2cookie`). Read `GLOSSARY.md` before naming things; decisions are in `docs/adr/`.

## Layout

- `pic2cookie/core/`: pure logic. `outline` (SVG to Ink), `trace` (raster to SVG), `roles` (Silhouette, features, Roles), `cutter` and `coaster` (layered 2D regions), `solid` (layers to meshes, Parts), `filament`, `export/` (STL, 3MF, Bambu project; several coloured Parts, pauses), `pipeline.make` / `make_coaster` tie them together.
- `pic2cookie/service.py`: Design operations shared by API, CLI and worker. `storage.py` (fs/S3 blobs, design.json/MongoDB records), `jobs.py` (inline/RQ), `settings.py` (`PIC2COOKIE_*` env).
- `pic2cookie/api.py` (FastAPI, also serves `frontend/dist`) and `pic2cookie/cli.py` (Typer).

## Conventions

- Heavy third-party modules are imported with `lazy import` (ADR-0001); keep `pic2cookie --help` fast.
- Geometry is 2D shapely, then extruded; no 3D booleans (ADR-0002).
- Docker is only built in GitHub Actions, never locally.
- The frontend is in English and German: every visible text is a key in `frontend/src/i18n.ts` (`de` must cover every `en` key); use the _German_ names from `GLOSSARY.md`.
- Warnings and errors the user can see are a `Notice` / `CodedError` with a code and params (English text for the CLI); add a `notice.<code>` string in both languages for each new code.
- Log with `logging.getLogger(__name__)` and pass context as `extra={...}` (`design_id`, ...); `pic2cookie/logs.py` formats it as text or JSON.

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
