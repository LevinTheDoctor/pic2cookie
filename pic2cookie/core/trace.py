"""Raster picture in, SVG out: the pixels in the Ink colour, traced as outlines."""

import io

lazy import cv2
lazy import numpy as np
lazy from PIL import Image, ImageOps, UnidentifiedImageError

from pic2cookie.core.model import CodedError, TraceParams
from pic2cookie.core.outline import parse_colour

MAX_SIDE = 2048  # larger pictures are scaled down before tracing
MIN_SIDE = 512  # smaller ones are scaled up for smoother outlines


class TraceError(CodedError):
    pass


def is_svg(data: bytes) -> bool:
    head = data[:2048].lstrip().lower()
    return head.startswith((b"<?xml", b"<svg", b"<!doctype svg")) or b"<svg" in head


def ink_mask(image, params: TraceParams) -> np.ndarray:
    """Boolean mask of the Ink pixels."""
    rgba = np.asarray(image.convert("RGBA"), dtype=np.float32)
    opaque = rgba[..., 3] > 127
    if params.ink == "alpha":
        mask = opaque
    else:
        ink = parse_colour(params.ink)
        if ink is None:
            raise TraceError("not_a_colour", f"Not a colour: {params.ink!r}", ink=params.ink)
        scale = np.sqrt(3) * 255  # as in colour_distance
        dist = np.linalg.norm(rgba[..., :3] - np.array(ink, np.float32), axis=-1) / scale
        mask = opaque & (dist <= params.tolerance)
    return ~mask if params.invert else mask


def trace(data: bytes, params: TraceParams | None = None) -> str:
    """Trace a PNG/JPG/WebP into an SVG with one even-odd filled path."""
    params = params or TraceParams()
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    except (UnidentifiedImageError, OSError) as e:
        raise TraceError("unsupported_image", "Not a supported image (PNG, JPG or WebP)") from e
    side = max(image.size)
    factor = MAX_SIDE / side if side > MAX_SIDE else min(4, MIN_SIDE / side) if side < MIN_SIDE else 1
    if factor != 1:
        size = (max(1, round(image.width * factor)), max(1, round(image.height * factor)))
        image = image.resize(size, Image.Resampling.LANCZOS)

    mask = ink_mask(image, params).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # A border keeps Ink touching the edge from being traced as open shapes.
    mask = cv2.copyMakeBorder(mask, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    contours, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    epsilon = max(0.3, params.smoothing) * max(1.0, factor)
    parts = []
    for contour in contours:
        if cv2.contourArea(contour) < 4 * factor * factor:
            continue
        pts = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2) - 1
        if len(pts) >= 3:
            parts.append("M" + "L".join(f"{x} {y}" for x, y in pts) + "Z")
    if not parts:
        raise TraceError("no_ink", "No Ink found; try another Ink colour, a higher tolerance or invert.")
    h, w = mask.shape[0] - 2, mask.shape[1] - 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
        f'<path fill="#000" fill-rule="evenodd" d="{"".join(parts)}"/>\n</svg>\n'
    )
