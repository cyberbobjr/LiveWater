"""Presentation board of the provisional tiles (ADR-001 D23, plan step E06).

Run after source/tiles/build_livewater_tiles.py:
    python -B tools/make_tile_board.py <render-dir> <out.png>
Lays out every base cell (no _E/_L/_N maps) grouped by part, with a label under
each cell, then the inventory items. The assembled network render stays its own image.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NAVY = (7, 35, 60)
CREAM = (254, 246, 225)
ORANGE = (240, 112, 20)
GROUND = (128, 150, 108)

GROUPS = [
    ("Pipes: 16 shapes (mask N=1 E=2 S=4 W=8)", r"pipe_m\d\d_S"),
    ("Shut-off valve (open, closed)", r"valve_.*"),
    ("Flow meter", r"flowmeter_.*"),
    ("Pond pump: off, on, with filter", r"pump_.*"),
    ("House inlet: filtered, unfiltered", r"house_inlet_.*"),
    ("Manual sprinkler: closed, open", r"sprinkler_manual_.*"),
    ("Automatic sprinkler: idle, watering", r"sprinkler_auto_.*"),
    ("Barrel fitting: Fill, Pump", r"barrel_.*"),
]
PER_ROW = 8


def font(size):
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main(render, out):
    cells = render / "cells"
    names = sorted(p.name[:-len("_x0_y0.png")] for p in cells.glob("*_x0_y0.png"))
    rows = []  # (title, [names])
    for title, pattern in GROUPS:
        picked = [n for n in names if re.fullmatch(pattern, n)]
        for i in range(0, len(picked), PER_ROW):
            rows.append((title if i == 0 else None, picked[i:i + PER_ROW]))
    items = sorted((render / "items").glob("*.png"))
    cw, ch, label, head, pad = 128, 256, 22, 34, 12
    width = pad + PER_ROW * (cw + pad)
    height = 70 + sum((head if t else 0) + ch + label + pad for t, _ in rows) + head + 160 + pad
    board = Image.new("RGB", (width, height), CREAM)
    d = ImageDraw.Draw(board)
    d.text((pad, 18), "LiveWater - provisional tiles (placeholder)", fill=NAVY, font=font(28))
    y = 70
    for title, group in rows:
        if title:
            d.text((pad, y + 6), title, fill=ORANGE, font=font(20))
            y += head
        for i, n in enumerate(group):
            x = pad + i * (cw + pad)
            d.rectangle((x, y, x + cw - 1, y + ch - 1), fill=GROUND)
            cell = Image.open(cells / (n + "_x0_y0.png")).convert("RGBA")
            board.paste(cell, (x, y), cell)
            d.text((x + 2, y + ch + 3), n.replace("sprinkler_", "spr_"), fill=NAVY, font=font(12))
        y += ch + label + pad
    d.text((pad, y + 6), "Inventory items", fill=ORANGE, font=font(20))
    y += head
    x = pad
    for p in items:
        icon = Image.open(p).convert("RGBA")
        icon.thumbnail((128, 128))
        board.paste(icon, (x, y), icon)
        d.text((x, y + 132), p.stem, fill=NAVY, font=font(12))
        x += 128 + pad * 3
    board.save(out)
    print("board:", out, board.size, len(names), "cells")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
