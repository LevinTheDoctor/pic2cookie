import io
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_bytes():
    return lambda name: (FIXTURES / name).read_bytes()


def png(draw_fn, size=(400, 400), mode="RGB", background="white") -> bytes:
    image = Image.new(mode, size, background)
    draw_fn(ImageDraw.Draw(image))
    buf = io.BytesIO()
    image.save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def donut_png() -> bytes:
    """A filled black donut with a hole and white sprinkles."""

    def draw(d):
        d.ellipse((20, 20, 380, 380), fill="black")
        d.ellipse((140, 140, 260, 260), fill="white")
        for x, y in ((90, 90), (280, 100), (300, 260), (100, 280)):
            d.rectangle((x, y, x + 30, y + 8), fill="white")

    return png(draw)


@pytest.fixture
def red_star_png() -> bytes:
    """A red star on a transparent background, next to a blue square."""

    def draw(d):
        d.polygon(
            [
                (200, 20),
                (240, 150),
                (380, 150),
                (265, 230),
                (310, 370),
                (200, 285),
                (90, 370),
                (135, 230),
                (20, 150),
                (160, 150),
            ],
            fill=(220, 30, 30, 255),
        )
        d.rectangle((0, 0, 40, 40), fill=(0, 0, 255, 255))

    return png(draw, mode="RGBA", background=(0, 0, 0, 0))
