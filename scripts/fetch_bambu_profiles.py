"""Flatten Bambu Studio's system presets into one project config per printer.

Run when adding a printer or updating presets:

    uv run python scripts/fetch_bambu_profiles.py

Writes pic2cookie/core/export/bambu_profiles/<printer>.json, each holding the
merged machine + process + filament settings that a Bambu Studio project
(Metadata/project_settings.config) carries.
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

REPO = "https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL"
TREE = "https://api.github.com/repos/bambulab/BambuStudio/git/trees/master?recursive=1"
OUT = Path(__file__).parent.parent / "pic2cookie/core/export/bambu_profiles"

PRINTERS = {
    "a1mini": ("Bambu Lab A1 mini 0.4 nozzle", "0.20mm Standard @BBL A1M"),
    "a1": ("Bambu Lab A1 0.4 nozzle", "0.20mm Standard @BBL A1"),
    "p1s": ("Bambu Lab P1S 0.4 nozzle", "0.20mm Standard @BBL X1C"),
    "p2s": ("Bambu Lab P2S 0.4 nozzle", "0.20mm Standard @BBL P2S"),
    "x1c": ("Bambu Lab X1 Carbon 0.4 nozzle", "0.20mm Standard @BBL X1C"),
    "h2d": ("Bambu Lab H2D 0.4 nozzle", "0.20mm Standard @BBL H2D"),
}
FILAMENTS = {"pla": "Bambu PLA Basic", "petg": "Bambu PETG Basic", "abs": "Bambu ABS"}

_cache: dict[tuple[str, str], dict] = {}


def fetch(kind: str, name: str) -> dict:
    if (kind, name) not in _cache:
        url = f"{REPO}/{kind}/{urllib.parse.quote(name)}.json"
        with urllib.request.urlopen(url) as r:
            _cache[kind, name] = json.load(r)
    return _cache[kind, name]


def resolve(kind: str, name: str) -> dict:
    """A preset with its `inherits` chain merged in (child wins)."""
    preset = fetch(kind, name)
    base = resolve(kind, preset["inherits"]) if preset.get("inherits") else {}
    return base | preset


def filament_for(base: str, machine: str, names: list[str]) -> str:
    """The system filament preset named `base @...` that lists `machine` as compatible."""
    for name in names:
        if name.startswith(f"{base} @") and machine in fetch("filament", name).get("compatible_printers", []):
            return name
    raise LookupError(f"No {base} preset for {machine}")


def filament_names() -> list[str]:
    with urllib.request.urlopen(TREE) as r:
        tree = json.load(r)["tree"]
    prefix = "resources/profiles/BBL/filament/"
    return sorted(
        t["path"][len(prefix) : -5]
        for t in tree
        if t["path"].startswith(prefix)
        and t["path"].endswith(".json")
        and "/" not in t["path"][len(prefix) :]
    )


def flatten(kind: str, name: str) -> dict:
    meta = {
        "inherits",
        "from",
        "instantiation",
        "setting_id",
        "type",
        "name",
        "version",
        "compatible_printers",
        "compatible_printers_condition",
        "filament_id",
        "include",
        "description",
    }
    return {k: v for k, v in resolve(kind, name).items() if k not in meta}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    names = [n for n in filament_names() if n.startswith(tuple(FILAMENTS.values()))]
    for key, (machine, process) in PRINTERS.items():
        machine_cfg = flatten("machine", machine)
        config = machine_cfg | flatten("process", process)
        filaments = {}
        for material, filament in FILAMENTS.items():
            try:
                name = filament_for(filament, machine, names)
            except LookupError:
                print(f"  {key}: no {filament} preset, skipped")  # e.g. ABS on open printers
                continue
            filaments[material] = {
                "name": name,
                "settings": flatten("filament", name),
                "filament_id": resolve("filament", name).get("filament_id"),
            }
        profile = {
            "printer_model": machine_cfg.get("printer_model"),
            "machine": machine,
            "process": process,
            "bed": machine_cfg.get("printable_area"),
            "height": machine_cfg.get("printable_height"),
            "config": config,
            "filaments": filaments,
        }
        (OUT / f"{key}.json").write_text(json.dumps(profile, indent=1, sort_keys=True))
        print(key, profile["printer_model"], profile["bed"], profile["height"])


if __name__ == "__main__":
    main()
