"""Cutter volume in, Filament estimate out."""

import math

from pic2cookie.core.model import DENSITY, FilamentEstimate, FilamentParams


def estimate(volume_mm3: float, params: FilamentParams) -> FilamentEstimate:
    """Filament for a solid print of `volume_mm3`; thin walls print practically solid."""
    grams = volume_mm3 / 1000 * DENSITY[params.material]
    metres = volume_mm3 / (math.pi * (params.diameter / 2) ** 2) / 1000
    cost = None if params.price_per_kg is None else round(grams / 1000 * params.price_per_kg, 2)
    return FilamentEstimate(
        material=params.material,
        volume_cm3=round(volume_mm3 / 1000, 2),
        grams=round(grams, 1),
        metres=round(metres, 2),
        cost=cost,
    )
