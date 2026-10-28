"""Command line interface (Typer)."""

import json
from pathlib import Path
from typing import Annotated

import typer
lazy import uvicorn

from pic2cookie.core.export import DEFAULT_PRINTER, Format, printers
from pic2cookie.core.model import (
    CoasterParams,
    Coin,
    CutterParams,
    FilamentParams,
    Material,
    Product,
    Role,
    TraceParams,
)

app = typer.Typer(help="Turn a picture into a 3D-printable cookie cutter or coaster.", no_args_is_help=True)
designs_app = typer.Typer(help="Work with saved Designs.", no_args_is_help=True)
app.add_typer(designs_app, name="designs")

FORMATS_BY_SUFFIX = {".stl": Format.STL, ".3mf": Format.THREEMF}


def _fail(message: str) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(1)


def _format_for(output: Path | None) -> Format:
    name = output.name.lower() if output else ""
    if name.endswith(".bambu.3mf"):
        return Format.BAMBU
    if name.endswith(".zip"):
        return Format.STL
    return FORMATS_BY_SUFFIX.get(output.suffix.lower() if output else "", Format.STL)


@app.command()
def make(
    picture: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="SVG, PNG, JPG or WebP")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Where to write the Product")] = None,
    fmt: Annotated[
        Format | None, typer.Option("--format", "-f", help="Defaults to the output's suffix")
    ] = None,
    product: Annotated[Product, typer.Option(help="What to make")] = Product.CUTTER,
    size: Annotated[
        float | None, typer.Option(help="Cutter: longest side, mm (80). Coaster: diameter or side (100)")
    ] = None,
    blade_height: Annotated[float, typer.Option(help="mm", rich_help_panel="Cutter")] = 15.0,
    blade_thickness: Annotated[float, typer.Option(help="mm", rich_help_panel="Cutter")] = 0.8,
    flange_width: Annotated[float, typer.Option(help="mm", rich_help_panel="Cutter")] = 4.0,
    flange_height: Annotated[float, typer.Option(help="mm", rich_help_panel="Cutter")] = 2.0,
    imprint_offset: Annotated[
        float, typer.Option(help="How much shorter Imprint blades are, mm", rich_help_panel="Cutter")
    ] = 3.0,
    support: Annotated[str, typer.Option(help="bridges or plate", rich_help_panel="Cutter")] = "bridges",
    min_hole: Annotated[
        float, typer.Option(help="Narrower holes become Imprint blades, mm", rich_help_panel="Cutter")
    ] = 8.0,
    min_imprint: Annotated[
        float, typer.Option(help="Smaller imprints are dropped, mm", rich_help_panel="Cutter")
    ] = 2.0,
    shape: Annotated[
        str, typer.Option(help="round, square, rounded or silhouette", rich_help_panel="Coaster")
    ] = "round",
    thickness: Annotated[float, typer.Option(help="Plate thickness, mm", rich_help_panel="Coaster")] = 4.0,
    margin: Annotated[
        float, typer.Option(help="Space around the Motif, mm", rich_help_panel="Coaster")
    ] = 10.0,
    motif_style: Annotated[
        str, typer.Option(help="inlay, raised or engraved", rich_help_panel="Coaster")
    ] = "inlay",
    motif_scale: Annotated[
        float, typer.Option(help="Share of the largest Motif that fits, 0-1", rich_help_panel="Coaster")
    ] = 1.0,
    invert_motif: Annotated[
        bool, typer.Option(help="The background becomes the Motif", rich_help_panel="Coaster")
    ] = False,
    plate_colour: Annotated[str, typer.Option(rich_help_panel="Coaster")] = "#ffffff",
    motif_colour: Annotated[str, typer.Option(rich_help_panel="Coaster")] = "#000000",
    rim: Annotated[bool, typer.Option(help="A lip along the edge", rich_help_panel="Coaster")] = False,
    feet: Annotated[bool, typer.Option(help="Foot recesses underneath", rich_help_panel="Coaster")] = False,
    opener: Annotated[
        str, typer.Option(help="Bottle opener: none, coin or plastic", rich_help_panel="Coaster")
    ] = "none",
    opener_side: Annotated[
        str, typer.Option(help="right, left, top or bottom", rich_help_panel="Coaster")
    ] = "right",
    coin: Annotated[Coin, typer.Option(help="The Coin insert", rich_help_panel="Coaster")] = Coin.EUR2,
    ink: Annotated[str, typer.Option(help='Ink colour of a raster picture, or "alpha"')] = "#000000",
    tolerance: Annotated[float, typer.Option(help="Colour distance still counted as Ink, 0-1")] = 0.35,
    invert: Annotated[bool, typer.Option(help="Swap Ink and background when tracing")] = False,
    role: Annotated[
        list[str] | None, typer.Option(help="Override a feature's Role, e.g. r3=hole or m2=ignore")
    ] = None,
    printer: Annotated[str, typer.Option(help="Bambu printer for --format bambu")] = DEFAULT_PRINTER,
    material: Annotated[Material, typer.Option()] = Material.PLA,
    price: Annotated[float | None, typer.Option(help="Filament price per kg")] = None,
    roles_svg: Annotated[Path | None, typer.Option(help="Cutter: also write the role-marked SVG")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print the result as JSON")] = False,
) -> None:
    """Make a Cutter or Coaster from a picture. Saves nothing but the files you ask for."""
    from pic2cookie.core.export import bed_warning, export
    from pic2cookie.core.pipeline import make as make_cutter
    from pic2cookie.core.pipeline import make_coaster

    fmt = fmt or _format_for(output)
    output = output or picture.with_name(picture.stem + fmt.filename(product).removeprefix(product.value))
    trace_params = TraceParams(ink=ink, tolerance=tolerance, invert=invert)
    filament_params = FilamentParams(material=material, price_per_kg=price)
    try:
        overrides = {k: Role(v) for k, v in (r.split("=", 1) for r in role or [])}
        if product is Product.COASTER:
            result = make_coaster(
                picture.read_bytes(),
                CoasterParams(
                    shape=shape,
                    size=size or 100.0,
                    thickness=thickness,
                    margin=margin,
                    motif_style=motif_style,
                    motif_scale=motif_scale,
                    invert=invert_motif,
                    plate_colour=plate_colour,
                    motif_colour=motif_colour,
                    rim=rim,
                    feet=feet,
                    opener=opener,
                    opener_side=opener_side,
                    coin=coin,
                ),
                trace_params,
                filament_params,
                overrides,
            )
            made, parts, pause_z = result.coaster, result.coaster.parts, result.coaster.pause_z
        else:
            result = make_cutter(
                picture.read_bytes(),
                CutterParams(
                    size=size or 80.0,
                    blade_height=blade_height,
                    blade_thickness=blade_thickness,
                    flange_width=flange_width,
                    flange_height=flange_height,
                    imprint_offset=imprint_offset,
                    support=support,
                    min_hole=min_hole,
                    min_imprint=min_imprint,
                ),
                trace_params,
                filament_params,
                overrides,
            )
            made, parts, pause_z = result.cutter, result.cutter.parts, None
        data = export(
            parts,
            fmt,
            name=picture.stem,
            product=product,
            printer_id=printer,
            material=material,
            pause_z=pause_z,
        )
    except ValueError as e:
        _fail(str(e))
    output.write_bytes(data)
    if roles_svg and product is Product.CUTTER:
        roles_svg.write_text(result.marked_svg)
    warnings = list(made.warnings)
    if fmt is Format.BAMBU and (warning := bed_warning(made.dimensions, printer)):
        warnings.append(warning)

    if as_json:
        typer.echo(
            json.dumps(
                {
                    "output": str(output),
                    "product": product.value,
                    "dimensions": made.dimensions.model_dump(),
                    "estimate": result.estimate.model_dump(),
                    "parts": [p.model_dump() for p in getattr(result, "parts", [])],
                    "pause_z": pause_z,
                    "features": [f.feature.model_dump(exclude={"path"}) for f in result.layout.features],
                    "warnings": warnings,
                },
                indent=2,
            )
        )
        return
    d, e = made.dimensions, result.estimate
    typer.echo(f"Wrote {output} ({d.width:g} x {d.depth:g} x {d.height:g} mm)")
    cost = f", {e.cost:.2f} per print" if e.cost is not None else ""
    typer.echo(f"Filament estimate: {e.grams:g} g / {e.metres:g} m {e.material.value.upper()}{cost}")
    for part in getattr(result, "parts", []):
        typer.echo(f"  {part.name:<6} {part.colour}  {part.estimate.grams:g} g")
    if pause_z is not None:
        typer.echo(f"Pause the print at {pause_z:g} mm and put the coin into its slot.")
    for fs in result.layout.features:
        f = fs.feature
        if f.role is not Role.IGNORE or f.default_role is not Role.IGNORE:
            typer.echo(f"  {f.id:>4}  {f.kind:<6}  {f.role.value}")
    for warning in warnings:
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
    from pic2cookie import logs
    from pic2cookie.settings import settings

    cfg = settings().log
    logs.setup(cfg)
    uvicorn.run(
        "pic2cookie.api:app",
        host=host,
        port=port,
        reload=reload,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_config=None,  # keep the handlers from logs.setup
        access_log=cfg.access,
    )


@app.command()
def worker(burst: Annotated[bool, typer.Option(help="Stop when the queue is empty")] = False) -> None:
    """Run an RQ worker (executor = rq)."""
    from pic2cookie import logs
    from pic2cookie.jobs import work
    from pic2cookie.settings import settings

    logs.setup(settings().log)
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
    """Copy a Design's files (picture, roles, Product) into a folder."""
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
