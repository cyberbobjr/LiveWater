"""Presentation board of the provisional tiles (ADR-001 D23, plan step E06).

Run after both steps of source/tiles/build_livewater_tiles.py (render, then style):
    set PZ_FORGE=E:\\pz-tools\\pz-sprite-forge
    set PZ_MEDIA=D:\\SteamLibrary\\steamapps\\common\\ProjectZomboid\\media
    python -B tools/make_tile_board.py <render-dir> <out.png>
First row: vanilla reference sprites, to judge coherence. Then every STYLED cell
(<render-dir>/styled) grouped by part, each on a vanilla grass tile with its label,
then the inventory icons (<render-dir>/styled_items, 64 px and 2x).
"""
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.environ.get("PZ_FORGE", r"E:\pz-tools\pz-sprite-forge"))
from pzforge.preview import DEFAULT_GAME_MEDIA, SpriteSource  # noqa: E402

NAVY = (7, 35, 60)
CREAM = (254, 246, 225)
ORANGE = (240, 112, 20)
BACKDROP = (70, 76, 64)
GRASS = "blends_natural_01_16"

VANILLA = ["street_decoration_01_12", "appliances_misc_01_4", "appliances_misc_01_8", "carpentry_02_54",
           "carpentry_02_122",
           "camping_01_16", "fixtures_sinks_01_4"]
#: (title, sprite name pattern, sprite drawn under each cell or None: overlays need their base)
GROUPS = [
    ("Pipes: 16 shapes (mask N=1 E=2 S=4 W=8)", r"pipe_m\d\d_S", None),
    ("Gate valve (open: stem up, closed: stem down)", r"valve_.*", None),
    ("Water meter", r"flowmeter_.*", None),
    ("Pond pump: off, on (32-39, the former filter tiles, unused since ADR-005)", r"pump_.*", None),
    ("House inlet: filtered (green), unfiltered (amber), with a filter cartridge (green, amber)", r"house_inlet_.*", None),
    ("Manual sprinkler: closed, open (no water: the jet is an animated overlay)", r"sprinkler_manual_.*", None),
    ("Automatic sprinkler: idle, watering", r"sprinkler_auto_.*", None),
    ("Sprinkler jet overlay, frames 0-5, facing S (cycled by the client)", r"sprinkler_jet\d_S",
     "sprinkler_manual_on_S"),
    ("Sprinkler jet overlay, frames 0-5, facing E", r"sprinkler_jet\d_E", "sprinkler_manual_on_E"),
    ("Barrel fitting: Fill over a barrel, Fill over a low crate, Pump (bottom spigot)", r"barrel_.*", None),
]
PER_ROW = 8
CW, CH, TOP = 128, 256, 96  # cells are drawn without their empty top 96 px


def font(size):
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def tile(sprite, grass):
    img = Image.new("RGBA", (CW, CH), BACKDROP + (255,))
    img.alpha_composite(grass)
    img.alpha_composite(sprite)
    return img.crop((0, TOP, CW, CH))


def main(render, out):
    media = Path(os.environ.get("PZ_MEDIA") or DEFAULT_GAME_MEDIA) / "texturepacks"
    vanilla = SpriteSource.from_packs([media / "Tiles2x.floor.pack", media / "Tiles2x.pack"])
    grass = vanilla.get(GRASS)
    styled = render / "styled"
    names = sorted(p.stem for p in styled.glob("*.png"))
    rows = [("Vanilla reference (game sprites, for comparison)", [(n, vanilla.get(n)) for n in VANILLA])]
    def cell(name, base):
        img = Image.open(styled / f"{name}.png").convert("RGBA")
        if base is None:
            return img
        under = Image.open(styled / f"{base}.png").convert("RGBA")
        under.alpha_composite(img)
        return under

    for title, pattern, base in GROUPS:
        picked = [n for n in names if re.fullmatch(pattern, n)]
        for i in range(0, len(picked), PER_ROW):
            rows.append((title if i == 0 else None, [(n, cell(n, base)) for n in picked[i:i + PER_ROW]]))
    items = sorted((render / "styled_items").glob("*.png"))
    ch, label, head, pad = CH - TOP, 22, 34, 12
    width = pad + PER_ROW * (CW + pad)
    height = 70 + sum((head if t else 0) + ch + label + pad for t, _ in rows) + head + 160 + pad
    board = Image.new("RGB", (width, height), CREAM)
    d = ImageDraw.Draw(board)
    d.text((pad, 18), "LiveWater - tiles (batman_livewater_01)", fill=NAVY, font=font(28))
    y = 70
    for title, group in rows:
        if title:
            d.text((pad, y + 6), title, fill=ORANGE, font=font(20))
            y += head
        for i, (n, sprite) in enumerate(group):
            x = pad + i * (CW + pad)
            board.paste(tile(sprite, grass), (x, y))
            d.text((x + 2, y + ch + 3), n.replace("sprinkler_", "spr_").replace("street_decoration", "street_deco"),
                   fill=NAVY, font=font(11))
        y += ch + label + pad
    d.text((pad, y + 6), "Inventory items", fill=ORANGE, font=font(20))
    y += head
    x = pad
    for p in items:
        icon = Image.open(p).convert("RGBA")
        board.paste(icon, (x, y), icon)
        big = icon.resize((128, 128), Image.NEAREST)
        board.paste(big, (x + 72, y), big)
        d.text((x, y + 132), p.stem, fill=NAVY, font=font(12))
        x += 200 + pad * 3
    board.save(out)
    print("board:", out, board.size, len(names), "cells")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
