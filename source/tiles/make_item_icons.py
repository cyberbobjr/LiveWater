"""Inventory icons of the LiveWater moveables (ADR-008 D12), cut from their styled tiles.

The crafting panel draws the icon of the script item (`Icon = LWT_<Part>` -> media/textures/Item_LWT_<Part>.png);
without one it shows a question mark. Each icon is the south-facing styled sprite of the part (step 2 of
build_livewater_tiles.py), cropped to its pixels, centred and scaled into 64 x 64 with a small margin.

    python source/tiles/make_item_icons.py <out>/styled .
"""
import sys
from pathlib import Path

from PIL import Image

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


def main(styled: Path, project: Path) -> None:
    textures = project / "Contents" / "mods" / "batman_LiveWater" / "42.21" / "media" / "textures"
    for part, name in SOURCES.items():
        target = textures / f"Item_LWT_{part}.png"
        icon(Image.open(styled / f"{name}.png")).save(target, optimize=True)
        print(target.name)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
