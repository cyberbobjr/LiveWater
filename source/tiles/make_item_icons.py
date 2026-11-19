"""Inventory icons of the LiveWater moveables (ADR-008 D12), cut from their styled tiles.

The crafting panel draws the icon of the script item (`Icon = LWT_<Part>` -> media/textures/Item_LWT_<Part>.png);
without one it shows a question mark. Each icon is the south-facing styled sprite of the part (step 2 of
build_livewater_tiles.py), cropped to its pixels, centred and scaled into 64 x 64 with a small margin.

    python source/tiles/make_item_icons.py <out>/styled .

The spent water filter (ADR-009 D01) is the water filter icon darkened and soiled: greyed folds, blackened charcoal,
a few grime spots (seeded, the same every run).

    python source/tiles/make_item_icons.py --spent .
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageEnhance

SIZE = 64
MARGIN = 3
#: part -> styled sprite (south facing, or the straight east-west shape)
SOURCES = {
    "Pipe": "pipe_m10_S",
    "PondPump": "pump_off_S",
    "Valve": "valve_open_ew_S",
    "FlowMeter": "flowmeter_ew_S",
    "HouseInlet": "house_inlet_S",
    "Sprinkler": "sprinkler_manual_off_S",
    "SprinklerAuto": "sprinkler_auto_off_S",
    "BarrelFitting": "barrel_fill_S",
    "DripLine": "drip_m10_S",
}


def icon(sprite: Image.Image) -> Image.Image:
    sprite = sprite.convert("RGBA")
    box = sprite.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    part = sprite.crop(box)
    side = SIZE - 2 * MARGIN
    scale = min(side / part.width, side / part.height)
    part = part.resize((max(1, round(part.width * scale)), max(1, round(part.height * scale))), Image.LANCZOS)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.alpha_composite(part, ((SIZE - part.width) // 2, (SIZE - part.height) // 2))
    return out


#: worn item -> icon it is made from
WORN = {"WaterFilterSpent": "WaterFilter"}
GRIME = (56, 46, 34)


def textures_of(project: Path) -> Path:
    return project / "Contents" / "mods" / "batman_LiveWater" / "42.21" / "media" / "textures"


def spent(new: Image.Image, seed: int = 9) -> Image.Image:
    """The icon of a worn-out item: less colour, darker, grime spots on its opaque pixels (alpha kept)."""
    new = new.convert("RGBA")
    alpha = new.getchannel("A")
    rgb = ImageEnhance.Color(new.convert("RGB")).enhance(0.35)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.7)
    rgb = ImageEnhance.Contrast(rgb).enhance(0.85)
    px = rgb.load()
    rng = random.Random(seed)
    w, h = rgb.size
    for _ in range(14):
        cx, cy, r = rng.randrange(w), rng.randrange(h), rng.uniform(1.5, 4.0)
        for y in range(max(0, int(cy - r)), min(h, int(cy + r) + 1)):
            for x in range(max(0, int(cx - r)), min(w, int(cx + r) + 1)):
                if alpha.getpixel((x, y)) > 8 and (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    k = 0.75 * (1 - ((x - cx) ** 2 + (y - cy) ** 2) / (r * r))
                    px[x, y] = tuple(round(c * (1 - k) + g * k) for c, g in zip(px[x, y], GRIME))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def main_spent(project: Path) -> None:
    textures = textures_of(project)
    for worn, new in WORN.items():
        target = textures / f"Item_LWT_{worn}.png"
        spent(Image.open(textures / f"Item_LWT_{new}.png")).save(target, optimize=True)
        print(target.name)


def main(styled: Path, project: Path) -> None:
    textures = textures_of(project)
    for part, name in SOURCES.items():
        target = textures / f"Item_LWT_{part}.png"
        icon(Image.open(styled / f"{name}.png")).save(target, optimize=True)
        print(target.name)


if __name__ == "__main__":
    if sys.argv[1] == "--spent":
        main_spent(Path(sys.argv[2]))
    else:
        main(Path(sys.argv[1]), Path(sys.argv[2]))
