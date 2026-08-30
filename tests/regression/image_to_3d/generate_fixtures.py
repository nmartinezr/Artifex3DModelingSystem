from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "generated"
SIZE = 256


def _canvas(alpha: bool = False, background: tuple[int, ...] | None = None) -> Image.Image:
    if alpha:
        return Image.new("RGBA", (SIZE, SIZE), background or (255, 255, 255, 0))
    return Image.new("RGB", (SIZE, SIZE), background or (245, 245, 245))


def render(recipe: str) -> Image.Image:
    alpha = recipe == "alpha-object"
    image = _canvas(alpha=alpha, background=(235, 235, 235) if recipe == "low-contrast" else None)
    draw = ImageDraw.Draw(image)
    ink = (45, 95, 155, 180) if alpha else (45, 95, 155)

    if recipe == "solid-box":
        draw.rounded_rectangle((60, 70, 196, 190), radius=12, fill=ink)
    elif recipe == "bottle":
        draw.rectangle((105, 45, 150, 72), fill=ink)
        draw.rounded_rectangle((82, 68, 174, 215), radius=28, fill=ink)
    elif recipe == "figure":
        draw.ellipse((96, 35, 160, 99), fill=ink)
        draw.rounded_rectangle((87, 92, 169, 190), radius=22, fill=ink)
        draw.rectangle((68, 105, 90, 175), fill=ink)
        draw.rectangle((166, 105, 188, 175), fill=ink)
        draw.rectangle((98, 185, 119, 230), fill=ink)
        draw.rectangle((137, 185, 158, 230), fill=ink)
    elif recipe == "quadruped":
        draw.ellipse((58, 88, 178, 170), fill=ink)
        draw.ellipse((165, 70, 220, 125), fill=ink)
        for x in (75, 110, 150, 185):
            draw.rectangle((x, 150, x + 16, 215), fill=ink)
        draw.line((60, 110, 30, 75), fill=ink, width=14)
    elif recipe == "offset-parts":
        draw.ellipse((45, 85, 145, 185), fill=ink)
        draw.polygon(((130, 125), (225, 75), (205, 190)), fill=ink)
    elif recipe == "antennae":
        draw.ellipse((75, 80, 181, 195), fill=ink)
        draw.line((105, 90, 75, 25), fill=ink, width=5)
        draw.line((150, 90, 188, 22), fill=ink, width=5)
    elif recipe == "concave-star":
        points = [(128, 25), (151, 91), (222, 91), (164, 132), (187, 205), (128, 160), (69, 205), (92, 132), (34, 91), (105, 91)]
        draw.polygon(points, fill=ink)
    elif recipe == "low-contrast":
        for offset in range(0, SIZE, 16):
            draw.line((0, offset, SIZE, offset), fill=(225, 225, 225), width=3)
        draw.ellipse((65, 55, 195, 205), fill=(205, 210, 215))
    elif recipe == "alpha-object":
        draw.rounded_rectangle((58, 62, 198, 198), radius=25, fill=ink)
    else:
        raise ValueError(f"Unknown fixture recipe: {recipe}")
    return image


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for case in MANIFEST["cases"]:
        image = render(case["recipe"])
        image.save(OUTPUT / f"{case['id']}.png", format="PNG", optimize=False)


if __name__ == "__main__":
    main()
