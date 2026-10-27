"""Command line interface (Typer)."""

import json
from pathlib import Path
from typing import Annotated

import typer
lazy import uvicorn

from pic2cookie.core.export import DEFAULT_PRINTER, Format, printers
from pic2cookie.core.model import CutterParams, FilamentParams, Material, Role, TraceParams

app = typer.Typer(help="Turn a picture into a 3D-printable cookie cutter.", no_args_is_help=True)
designs_app = typer.Typer(help="Work with saved Designs.", no_args_is_help=True)
app.add_typer(designs_app, name="designs")

FORMATS_BY_SUFFIX = {".stl": Format.STL, ".3mf": Format.THREEMF}


def _fail(message: str) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(1)


@app.command()
def make(
    picture: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="SVG, PNG, JPG or WebP")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Where to write the Cutter")] = None,
    fmt: Annotated[
        Format | None, typer.Option("--format", "-f", help="Defaults to the output's suffix")
    ] = None,
    size: Annotated[float, typer.Option(help="Longest side of the Silhouette, mm")] = 80.0,
    blade_height: Annotated[float, typer.Option(help="mm")] = 15.0,
    blade_thickness: Annotated[float, typer.Option(help="mm")] = 0.8,
    flange_width: Annotated[float, typer.Option(help="mm")] = 4.0,
    flange_height: Annotated[float, typer.Option(help="mm")] = 2.0,
    imprint_offset: Annotated[float, typer.Option(help="How much shorter Imprint blades are, mm")] = 3.0,
    support: Annotated[str, typer.Option(help="bridges or plate")] = "bridges",
    min_hole: Annotated[float, typer.Option(help="Narrower holes become Imprint blades, mm")] = 8.0,
    min_imprint: Annotated[float, typer.Option(help="Smaller imprints are dropped, mm")] = 2.0,
    ink: Annotated[str, typer.Option(help='Ink colour of a raster picture, or "alpha"')] = "#000000",
    tolerance: Annotated[float, typer.Option(help="Colour distance still counted as Ink, 0-1")] = 0.35,
    invert: Annotated[bool, typer.Option(help="Swap Ink and background")] = False,
    role: Annotated[list[str] | None, typer.Option(help="Override a feature's Role, e.g. r3=hole")] = None,
    printer: Annotated[str, typer.Option(help="Bambu printer for --format bambu")] = DEFAULT_PRINTER,
    material: Annotated[Material, typer.Option()] = Material.PLA,
    price: Annotated[float | None, typer.Option(help="Filament price per kg")] = None,
    roles_svg: Annotated[Path | None, typer.Option(help="Also write the role-marked SVG here")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print the result as JSON")] = False,
) -> None:
    """Make a Cutter from a picture. Saves nothing but the files you ask for."""
    from pic2cookie.core.export import export
    from pic2cookie.core.pipeline import make as run

    if fmt is None:
        name = output.name.lower() if output else ""
        fmt = (
            Format.BAMBU
            if name.endswith(".bambu.3mf")
            else FORMATS_BY_SUFFIX.get(output.suffix.lower() if output else "", Format.STL)
        )
    output = output or picture.with_suffix("." + fmt.filename.split(".", 1)[1])
    try:
        overrides = {k: Role(v) for k, v in (r.split("=", 1) for r in role or [])}
        result = run(
            picture.read_bytes(),
            CutterParams(
                size=size,
                blade_height=blade_height,
                blade_thickness=blade_thickness,
                flange_width=flange_width,
                flange_height=flange_height,
                imprint_offset=imprint_offset,
                support=support,
                min_hole=min_hole,
                min_imprint=min_imprint,
            ),
            TraceParams(ink=ink, tolerance=tolerance, invert=invert),
            FilamentParams(material=material, price_per_kg=price),
            overrides,
        )
        data = export(result.cutter.mesh, fmt, name=picture.stem, printer_id=printer, material=material)
    except ValueError as e:
        _fail(str(e))
    output.write_bytes(data)
    if roles_svg:
        roles_svg.write_text(result.marked_svg)

    if as_json:
        typer.echo(
            json.dumps(
                {
                    "output": str(output),
                    "dimensions": result.cutter.dimensions.model_dump(),
                    "estimate": result.estimate.model_dump(),
                    "features": [f.feature.model_dump(exclude={"path"}) for f in result.layout.features],
                    "warnings": result.cutter.warnings,
                },
                indent=2,
            )
        )
        return
    d, e = result.cutter.dimensions, result.estimate
    typer.echo(f"Wrote {output} ({d.width:g} x {d.depth:g} x {d.height:g} mm)")
    cost = f", {e.cost:.2f} per print" if e.cost is not None else ""
    typer.echo(f"Filament estimate: {e.grams:g} g / {e.metres:g} m {e.material.value.upper()}{cost}")
    for fs in result.layout.features:
        f = fs.feature
        if f.role is not Role.IGNORE or f.default_role is not Role.IGNORE:
            typer.echo(f"  {f.id:>4}  {f.kind:<6}  {f.role.value}")
    for warning in result.cutter.warnings:
        typer.secho(f"Warning: {warning}", fg=typer.colors.YELLOW)


@app.command()
def trace(
    picture: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="PNG, JPG or WebP")],
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    ink: Annotated[str, typer.Option(help='Ink colour, or "alpha"')] = "#000000",
    tolerance: Annotated[float, typer.Option()] = 0.35,
    invert: Annotated[bool, typer.Option()] = False,
    smoothing: Annotated[float, typer.Option(help="Outline simplification, px")] = 1.0,
) -> None:
    """Trace a raster picture into an SVG."""
    from pic2cookie.core.trace import trace as run

    output = output or picture.with_suffix(".svg")
    try:
        svg = run(
            picture.read_bytes(),
            TraceParams(ink=ink, tolerance=tolerance, invert=invert, smoothing=smoothing),
        )
    except ValueError as e:
        _fail(str(e))
    output.write_text(svg)
    typer.echo(f"Wrote {output}")


@app.command("printers")
def list_printers() -> None:
    """List the Bambu printers for --printer."""
    for p in printers():
        mats = ", ".join(m.value for m in p.materials)
        typer.echo(f"{p.id:<7} {p.name:<22} {p.bed[0]:g} x {p.bed[1]:g} mm  ({mats})")


@app.command()
def serve(
    host: Annotated[str, typer.Option(envvar="PIC2COOKIE_HOST")] = "127.0.0.1",
    port: Annotated[int, typer.Option(envvar="PIC2COOKIE_PORT")] = 8000,
    reload: Annotated[bool, typer.Option(help="Restart on code changes")] = False,
) -> None:
    """Run the API and the built frontend."""
    uvicorn.run(
        "pic2cookie.api:app", host=host, port=port, reload=reload, proxy_headers=True, forwarded_allow_ips="*"
    )


@app.command()
def worker(burst: Annotated[bool, typer.Option(help="Stop when the queue is empty")] = False) -> None:
    """Run an RQ worker (executor = rq)."""
    from pic2cookie.jobs import work

    work(burst=burst)


@designs_app.command("ls")
def designs_ls() -> None:
    """List saved Designs."""
    from pic2cookie.service import service

    for d in service().list():
        grams = f"{d.result.estimate.grams:g} g" if d.result else "-"
        typer.echo(f"{d.id}  {d.updated:%Y-%m-%d %H:%M}  {d.status:<6}  {grams:>8}  {d.name}")


@designs_app.command("show")
def designs_show(design_id: str) -> None:
    """Show a Design as JSON."""
    from pic2cookie.service import service
    from pic2cookie.storage import NotFound

    try:
        typer.echo(service().get(design_id).model_dump_json(indent=2))
    except NotFound:
        _fail(f"No Design {design_id}")


@designs_app.command("rm")
def designs_rm(design_ids: list[str], yes: Annotated[bool, typer.Option("--yes", "-y")] = False) -> None:
    """Delete Designs and their files."""
    from pic2cookie.service import service
    from pic2cookie.storage import NotFound

    if not yes:
        typer.confirm(f"Delete {len(design_ids)} Design(s)?", abort=True)
    for design_id in design_ids:
        try:
            service().delete(design_id)
            typer.echo(f"Deleted {design_id}")
        except NotFound:
            typer.secho(f"No Design {design_id}", fg=typer.colors.YELLOW, err=True)


@designs_app.command("export")
def designs_export(
    design_id: str,
    output: Annotated[Path, typer.Option("--output", "-o", file_okay=False)] = Path("."),
) -> None:
    """Copy a Design's files (picture, roles, Cutter) into a folder."""
    from pic2cookie.service import service
    from pic2cookie.storage import NotFound

    try:
        names = service().files(design_id)
        output.mkdir(parents=True, exist_ok=True)
        for name in names:
            (output / name).write_bytes(service().file(design_id, name))
            typer.echo(f"Wrote {output / name}")
    except NotFound:
        _fail(f"No Design {design_id}")


if __name__ == "__main__":
    app()
