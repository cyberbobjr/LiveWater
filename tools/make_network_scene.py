r"""Example network in context (ADR-001 D23, plan step E06): the styled provisional tiles
placed on vanilla ground next to vanilla objects, as the game would draw them.

Pond -> pump -> gate valve -> tee to the rain barrel -> water meter -> tee to the house
inlet (on a house wall) and to a manual and an automatic sprinkler.
Run after the style step of source/tiles/build_livewater_tiles.py:
    set PZ_FORGE=E:\pz-tools\pz-sprite-forge
    set PZ_MEDIA=D:\SteamLibrary\steamapps\common\ProjectZomboid\media
    python -B tools/make_network_scene.py <render-dir> <out.png>
Grid: i grows east (screen down-right), j grows south (screen down-left).
"""
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, os.environ.get("PZ_FORGE", r"E:\pz-tools\pz-sprite-forge"))
from pzforge.preview import DEFAULT_GAME_MEDIA, SpriteSource, compose  # noqa: E402

COLS, ROWS = 9, 7
GRASS, WATER, DIRT = "blends_natural_01_16", "blends_natural_02_0", "blends_natural_01_64"
WALL_N = "walls_exterior_house_01_1"
POND = {(0, 4), (1, 4), (2, 4), (0, 5), (1, 5), (2, 5), (3, 5), (0, 6), (1, 6), (2, 6), (3, 6), (4, 6)}
PLOT = {(4, 4), (5, 4), (6, 4), (4, 5), (5, 5), (6, 5)}

#: (i, j, styled sprite or "vanilla:<name>"), drawn after the floors of the same tile.
LAYOUT = [
    (1, 3, "pump_filter_on_S"),
    (1, 2, "pipe_m06_S"),              # S | E
    (2, 2, "valve_open_ew_S"),
    (3, 2, "pipe_m11_S"),              # N | E | W
    (3, 1, "barrel_fill_S"),
    (3, 0, "vanilla:carpentry_02_54"),
    (4, 2, "flowmeter_ew_S"),
    (5, 2, "pipe_m15_S"),              # cross
    (5, 1, "vanilla:" + WALL_N), (6, 1, "vanilla:" + WALL_N), (7, 1, "vanilla:" + WALL_N),
    (5, 1, "house_inlet_S"),
    (6, 2, "pipe_m08_S"),              # W, capped
    (5, 3, "pipe_m13_S"),              # N | S | W
    (5, 4, "sprinkler_manual_on_N"),
    (7, 3, "vanilla:appliances_misc_01_8"),
    (4, 3, "sprinkler_auto_off_E"),
]


def main(render: Path, out: Path) -> None:
    media = Path(os.environ.get("PZ_MEDIA") or DEFAULT_GAME_MEDIA) / "texturepacks"
    vanilla = SpriteSource.from_packs([media / "Tiles2x.floor.pack", media / "Tiles2x.pack"])

    def sprite(name):
        if name.startswith("vanilla:"):
            return vanilla.get(name[len("vanilla:"):])
        return Image.open(render / "styled" / f"{name}.png").convert("RGBA")

    placements = []
    for i in range(COLS):
        for j in range(ROWS):
            floor = WATER if (i, j) in POND else DIRT if (i, j) in PLOT else GRASS
            placements.append((i, j, vanilla.get(floor)))
    placements += [(i, j, sprite(name)) for i, j, name in LAYOUT]
    scene = compose(placements, COLS, ROWS, background=(40, 44, 36, 255))
    scene = scene.crop((0, 140, scene.width, scene.height - 50))  # empty margin above the ground
    scene.convert("RGB").save(out)
    print("scene:", out, scene.size)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
