"""3D models of the LiveWater tiles for Viewpoint (ADR-019), from the same Blender builders as the tiles.

Viewpoint 0.1.7 discovers the resource pack itself in the sub-mod batman_LiveWaterViewpoint:
    common/media/viewpoint/resourcepacks/batman-livewater/
        pack.properties     descriptor (format 1)
        models.properties   model.<name>=models/<name>.obj, bind.<sprite>=<name>,0,0,0,0,1
        icon.png            pack icon in Viewpoint's menu
        models/*.obj        one model per tile group (its S facing); the binds turn it for E, N and W
        models/livewater.mtl  one material per paint, all on the palette texture; lit lamps glow (Ke)
        models/palette.png    one 8 x 8 px swatch per paint

Run headless (no render, no forge rig):
    blender -b --factory-startup -P source/tiles/build_viewpoint_models.py -- [<project-root>]

Axes: Blender (1 m = 1 tile, tile centre at the origin, +Y north) -> Viewpoint OBJ (X east, Y south, Z up):
(x, y, z) is written (x, -y, z); the mirror turns the faces inside out, so their corners are written reversed.
"""
from __future__ import annotations

import os
import struct
import sys
import zlib
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_livewater_tiles as T  # noqa: E402

SUB_MOD = "batman_LiveWaterViewpoint"
PACK_ID = "batman-livewater"
PACK_VERSION = "1.0.0"
MTL = "livewater.mtl"
PALETTE = "palette.png"
SWATCH, GRID = 8, 8
# Not bound (ADR-019 D04): the invisible relay has no group; the animated jet is an overlay group (skipped).

DESCRIPTOR = f"""format=1
id={PACK_ID}
name=LiveWater
version={PACK_VERSION}
author=batmanfr
description=3D models of the LiveWater pump, pipes, valves, water meter, house inlet, sprinklers, fittings and drip line.
license=MIT
icon=icon.png
game.min=42.22
viewpoint.min=0.1.7
models=models.properties
"""


def srgb(c: float) -> int:
    c = max(0.0, min(1.0, c))
    s = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return round(255 * s)


def paint_colours() -> dict:
    """Linear colour of every paint (the forge paints; brass halfway between its dark and light tones)."""
    out = {}
    for key, (_, paint, opts) in T.PAINTS.items():
        if paint is None:
            dark, light = opts["dark"], opts["light"]
            paint = tuple((a + b) / 2 for a, b in zip(dark, light))
        out[key] = paint
    for key, colour in T.LIT.items():
        out[f"lit_{key}"] = colour
    return out


def write_png(path: Path, width: int, height: int, rows: list[bytes]) -> None:
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + r for r in rows)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    path.write_bytes(png)


def write_palette(folder: Path, colours: dict) -> dict:
    """palette.png and livewater.mtl; returns paint -> (u, v) of its swatch centre (OBJ v counts from the bottom)."""
    names = sorted(colours)
    if len(names) > GRID * GRID:
        raise SystemExit("more paints than palette swatches")
    side = SWATCH * GRID
    pixels = [[(0, 0, 0)] * side for _ in range(side)]
    uv, mtl = {}, []
    for k, name in enumerate(names):
        col, row = k % GRID, k // GRID
        rgb = tuple(srgb(c) for c in colours[name])
        for y in range(row * SWATCH, (row + 1) * SWATCH):
            for x in range(col * SWATCH, (col + 1) * SWATCH):
                pixels[y][x] = rgb
        uv[name] = ((col + 0.5) / GRID, 1.0 - (row + 0.5) / GRID)
        mtl += [f"newmtl {name}", "Kd 1 1 1", "d 1", f"map_Kd {PALETTE}"]
        if name.startswith("lit_"):
            mtl.append("Ke " + " ".join(f"{c:.3f}" for c in colours[name]))
        mtl.append("")
    write_png(folder / PALETTE, side, side, [bytes(v for p in r for v in p) for r in pixels])
    (folder / MTL).write_text("\n".join(mtl), encoding="ascii", newline="\n")
    return uv


class Paints(dict):
    """Kit materials: one plain Blender material per paint key, named after it."""

    def __missing__(self, key):
        mat = bpy.data.materials.get(key) or bpy.data.materials.new(key)
        self[key] = mat
        return mat


def meshes(root) -> list:
    out, stack = [], list(root.children)
    while stack:
        obj = stack.pop()
        stack.extend(obj.children)
        if obj.type == "MESH":
            out.append(obj)
    return sorted(out, key=lambda o: o.name)


def fmt(x: float) -> str:
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def export_obj(path: Path, root, uv: dict) -> None:
    """World-space geometry of every mesh under `root`, mirrored to Viewpoint's axes. Normals are written once
    each, when a face first needs them (a face only uses lines declared before it)."""
    lines = ["# LiveWater for Viewpoint: Z up, tile units, X east, Y south, origin at the tile centre",
             f"mtllib {MTL}"]
    nv = 0
    normals = {}
    vt_index = {}
    for name in sorted(uv):
        u, v = uv[name]
        lines.append(f"vt {fmt(u)} {fmt(v)}")
        vt_index[name] = len(vt_index) + 1

    def normal(vec) -> int:
        n = vec.normalized()
        key = f"{fmt(n.x)} {fmt(-n.y)} {fmt(n.z)}"
        if key not in normals:
            normals[key] = len(normals) + 1
            lines.append(f"vn {key}")
        return normals[key]

    for obj in meshes(root):
        me, mw = obj.data, obj.matrix_world
        nm = mw.to_3x3().inverted().transposed()
        lines.append(f"o {obj.name}")
        for v in me.vertices:
            p = mw @ v.co
            lines.append(f"v {fmt(p.x)} {fmt(-p.y)} {fmt(p.z)}")
        base_v = nv
        nv += len(me.vertices)
        current = None
        for poly in me.polygons:
            paint = obj.material_slots[poly.material_index].material.name
            if paint != current:
                lines.append(f"usemtl {paint}")
                current = paint
            t = vt_index[paint]
            if poly.use_smooth:
                corners = [f"{base_v + i + 1}/{t}/{normal(nm @ me.vertices[i].normal)}" for i in poly.vertices]
            else:
                flat = normal(nm @ poly.normal)
                corners = [f"{base_v + i + 1}/{t}/{flat}" for i in poly.vertices]
            lines.append("f " + " ".join(reversed(corners)))
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def write_icon(project: Path, pack: Path) -> None:
    img = bpy.data.images.load(str(project / "preview.png"))
    img.scale(128, 128)
    img.filepath_raw = str(pack / "icon.png")
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def facing_degrees(f: int) -> int:
    """Bind angle of facing f (S, E, N, W). The forge turns the S model 90 degrees counter-clockwise (seen from
    above) per facing. Viewpoint turns a bound model (viewpoint.packs.PackBind, its axes x = -X, z = -Y) so that,
    in OBJ axes, (X, Y) -> (X cos a - Y sin a, X sin a + Y cos a): +90 takes east to south, clockwise on the
    map. The forge's turn is therefore -90 degrees per facing."""
    return (-90 * f) % 360


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    project = Path(args[0] if args else Path(__file__).resolve().parents[2]).resolve()
    pack = project / "Contents" / "mods" / SUB_MOD / "common" / "media" / "viewpoint" / "resourcepacks" / PACK_ID
    models_dir = pack / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    for old in models_dir.glob("*.obj"):
        old.unlink()
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene = bpy.context.scene
    subject = bpy.data.objects.new("LWT_Subject", None)
    scene.collection.objects.link(subject)
    uv = write_palette(models_dir, paint_colours())
    mats = Paints()
    manifest = ["# LiveWater models for Viewpoint (ADR-019), written by source/tiles/build_viewpoint_models.py"]
    binds = []
    for group in T.tile_groups():
        if group["overlay"]:
            continue
        T.clear_subject(subject)
        (group["lit"] or group["build"])(T.Kit(subject, mats))
        bpy.context.view_layer.update()
        name = group["key"]
        export_obj(models_dir / f"{name}.obj", subject, uv)
        manifest.append(f"model.{name}=models/{name}.obj")
        for f, index in enumerate(group["indices"]):
            binds.append((index, f"bind.{T.SHEET}_{index}={name},{facing_degrees(f)},0,0,0,1"))
    T.clear_subject(subject)
    manifest += [line for _, line in sorted(binds)]
    (pack / "models.properties").write_text("\n".join(manifest) + "\n", encoding="ascii", newline="\n")
    (pack / "pack.properties").write_text(DESCRIPTOR, encoding="ascii", newline="\n")
    write_icon(project, pack)
    print(f"viewpoint pack: {len(binds)} sprites into {pack}")


if __name__ == "__main__":
    main()
