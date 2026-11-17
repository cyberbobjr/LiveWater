"""Provisional tiles of LiveWater, for the D23 presentation board (plan step E06).

Board validated by the user on 2026-11-17 (ADR-001 D23), packed into the mod since E06.
The sprinkler jet is a separate 6-frame overlay (indices 80-103) that the client swaps
itself (ADR-001 D08a): the engine never advances the frames of a tile overlay.

Look: 1990s rural hardware drawn like vanilla tile art. Galvanised pipe with thin
couplings, brass gate valve with a red handwheel, bronze water meter, electric
centrifugal pump on a wooden skid, wall-mounted inlet box, impact sprinkler on a
riser, garden hose to a rain barrel. Every part uses a textured pz-sprite-forge
material class (wear streaks, rust or patina accents), and every group goes
through the pzforge style pass (tone bands, paint flattening, strokes, grain,
contours), like the accepted Live Wire tiles.

Needs pz-sprite-forge (MIT) and the game (PZ_MEDIA) for the style pass.
1. Render every group, headless (each into <out>/cells/<key>/ with its manifest):
       set PZ_FORGE=E:\\pz-tools\\pz-sprite-forge
       blender -b --factory-startup -P source/tiles/build_livewater_tiles.py -- <out> [<key>...]
   Lights and the sprinkler spray render as separate overlays (<key>__lit), the
   inventory items into <out>/items/.
2. Style (Python with Pillow):
       set PZ_MEDIA=D:\\SteamLibrary\\steamapps\\common\\ProjectZomboid\\media
       python source/tiles/build_livewater_tiles.py style <out> [<key>...]
   -> <out>/styled/<key>_<facing>.png (128x256, the sprites shown on the board)
      <out>/styled_items/<item>.png
3. Package into the mod (tileset batman_livewater_01, tiledef 7176, indices of
   docs/annexes/conception/tuiles-contrat.md):
       python source/tiles/build_livewater_tiles.py package <out> .
   -> Contents/mods/batman_LiveWater/common/media/texturepacks/batman_livewater_01.pack,
      common/media/batman_livewater_01.tiles, common/media/tileGeometry.txt,
      42.21/media/textures/Item_LWT_PipeSection.png, Item_LWT_WaterFilter.png
4. Depth map (skill pz-blender-assets, scripts/build_depthmap.py):
       blender -b --factory-startup -P <skill>/scripts/build_depthmap.py -- source/tiles/build_livewater_tiles.py <out>/depth.json
       python <skill>/scripts/build_depthmap.py <out>/depth.json
           Contents/mods/batman_LiveWater/common/media/texturepacks/batman_livewater_01.pack batman_livewater_01
           Contents/mods/batman_LiveWater/common/media/depthmaps/DEPTH_batman_livewater_01.png
5. Board and example scene: tools/make_tile_board.py, tools/make_network_scene.py.

Conventions: 1 Blender metre = 1 tile, tile centre at the origin, front (S) toward
-Y. Pipe sides are a 4-bit mask: N=1, E=2, S=4, W=8.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

try:
    import bpy
    from mathutils import Vector
except ImportError:  # style step, plain Python
    bpy = None

FORGE = Path(os.environ.get("PZ_FORGE", r"E:\pz-tools\pz-sprite-forge"))
sys.path.insert(0, str(FORGE / "blender"))
sys.path.insert(0, str(FORGE))
if bpy is not None:
    import pz_sprite_forge as F  # noqa: E402

N, E, S, W = 1, 2, 4, 8
DIRS = {N: (0, 1), E: (1, 0), S: (0, -1), W: (-1, 0)}

PIPE_R = 0.034    # 1 in galvanised pipe, drawn about twice real size to read at play distance
PIPE_Z = PIPE_R + 0.012   # laid on the ground
COUP_R = 0.043    # threaded coupling / fitting
WALL_Y = 0.465    # back of wall-mounted parts (N wall face)


# --------------------------------------------------------------------------- #
# Materials (stage 1): textured forge classes, realistic colours
# --------------------------------------------------------------------------- #

def _same(p):
    return p


#: key -> (class, paint, extra forge_material options); "tex" picks the detail map.
PAINTS = {
    "galv": ("metal", (0.40, 0.41, 0.40), {"tex": "metal", "accent": (0.30, 0.25, 0.20), "accent_position": 0.08}),
    "galv_dark": ("metal", (0.22, 0.23, 0.22), {"tex": "metal", "accent": (0.22, 0.16, 0.11),
                                                "accent_position": 0.08}),
    "iron": ("metal", (0.17, 0.17, 0.16), {"tex": "metal", "accent": (0.17, 0.10, 0.06), "accent_position": 0.10}),
    "motor": ("metal", (0.20, 0.29, 0.33), {"tex": "metal", "accent": (0.16, 0.12, 0.09), "accent_position": 0.06,
                                            "hue": _same}),
    "brass": ("metal", None, {"tex": "metal", "dark": (0.20, 0.12, 0.035), "light": (0.55, 0.38, 0.12),
                              "accent": (0.13, 0.17, 0.11), "accent_position": 0.10, "hue": _same}),
    "red": ("metal", (0.36, 0.035, 0.025), {"tex": "metal", "hue": _same}),
    "box": ("metal", (0.36, 0.37, 0.33), {"tex": "metal", "hue": _same}),
    "rubber": ("fabric", (0.025, 0.025, 0.025), {}),
    "hose": ("fabric", (0.05, 0.15, 0.06), {}),
    "plastic": ("fabric", (0.13, 0.17, 0.13), {}),
    "bowl": ("fabric", (0.30, 0.42, 0.50), {}),
    "dial": ("fabric", (0.62, 0.60, 0.52), {}),
    "needle": ("fabric", (0.45, 0.04, 0.03), {}),
    "lamp": ("fabric", (0.05, 0.06, 0.05), {}),
    "paper": ("fabric", (0.62, 0.58, 0.46), {}),
    "wood": ("wood", (0.24, 0.18, 0.12), {"tex": "wood"}),
    "board": ("wood", (0.27, 0.25, 0.21), {"tex": "wood"}),
}

#: Overlay paints: lit lamps and water (raw colours, composited after the style pass).
LIT = {"green": (0.30, 1.0, 0.35), "amber": (1.0, 0.62, 0.10)}
WATER = {"jet": ((0.62, 0.80, 0.95), 0.85), "mist": ((0.66, 0.82, 0.95), 0.40)}


def textures(out_dir: Path) -> dict:
    """Detail maps from the forge's measured material grammars."""
    from pzforge.texture import material_spec, write_surface_map
    return {
        "metal": write_surface_map(out_dir / "lwt_metal.png", 512, 256, material_spec("metal", seed=31)),
        "wood": write_surface_map(out_dir / "lwt_wood.png", 512, 256, material_spec("wood", seed=12),
                                  grain_axis="u"),
    }


def water_material(name, colour, alpha):
    """Unlit, semi-transparent water (overlay only)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*colour, 1.0)
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = alpha
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(emit.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def materials(tex_dir: Path | None = None) -> dict:
    maps = textures(Path(tex_dir or Path(bpy.app.tempdir or ".")))
    mats = {}
    for key, (cls, paint, opts) in PAINTS.items():
        opts = dict(opts)
        tex = opts.pop("tex", None)
        kwargs = {"texture_path": str(maps[tex]), "projection": "BOX", "texture_scale": 3.0} if tex else {}
        mats[key] = F.forge_material(f"lwt_{key}", cls, paint, **kwargs, **opts)
    for key, colour in LIT.items():
        mats[f"lit_{key}"] = F.forge_material(f"lwt_lit_{key}", "fabric", colour)
    for key, (colour, alpha) in WATER.items():
        mats[f"water_{key}"] = water_material(f"lwt_water_{key}", colour, alpha)
    return mats


# --------------------------------------------------------------------------- #
# Mesh kit (data API only: headless and in a dedicated MCP scene)
# --------------------------------------------------------------------------- #

AXIS_ROT = {"x": (0, math.pi / 2, 0), "y": (math.pi / 2, 0, 0), "z": (0, 0, 0)}


class Kit:
    """Parts parented to an anchor (the forge subject or a sub-empty)."""

    def __init__(self, anchor, mats):
        self.anchor, self.mats = anchor, mats

    def empty(self, name, loc=(0, 0, 0), rot=(0, 0, 0)) -> "Kit":
        obj = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent, obj.location, obj.rotation_euler = self.anchor, loc, rot
        return Kit(obj, self.mats)

    def mesh(self, name, verts, faces, mat, loc=(0, 0, 0), rot=(0, 0, 0), smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.update()
        if smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(self.mats[mat])
        obj.parent, obj.location, obj.rotation_euler = self.anchor, loc, rot
        return obj

    def box(self, name, c, size, mat, rot=(0, 0, 0)):
        sx, sy, sz = (s / 2 for s in size)
        verts = [(x, y, z) for z in (-sz, sz) for y in (-sy, sy) for x in (-sx, sx)]
        faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        return self.mesh(name, verts, faces, mat, c, rot)

    def cyl(self, name, c, r, depth, mat, axis="z", segs=16, rot=None, r2=None):
        """Cylinder (or cone with r2) along a local axis."""
        r2 = r if r2 is None else r2
        verts = [(rr * math.cos(2 * math.pi * j / segs), rr * math.sin(2 * math.pi * j / segs), z)
                 for z, rr in ((-depth / 2, r), (depth / 2, r2)) for j in range(segs)]
        faces = [(j, (j + 1) % segs, segs + (j + 1) % segs, segs + j) for j in range(segs)]
        faces += [tuple(reversed(range(segs))), tuple(range(segs, 2 * segs))]
        return self.mesh(name, verts, faces, mat, c, rot or AXIS_ROT[axis], smooth=segs > 8)

    def rod(self, name, p0, p1, r, mat, segs=12):
        a, b = Vector(p0), Vector(p1)
        obj = self.cyl(name, (0, 0, 0), r, (b - a).length, mat, segs=segs)
        obj.location = (a + b) / 2
        obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
        return obj

    def ball(self, name, c, r, mat, segs=12):
        rings = max(4, segs // 2)
        verts = [(0, 0, -r)]
        for i in range(1, rings):
            phi = math.pi * i / rings - math.pi / 2
            verts += [(r * math.cos(phi) * math.cos(2 * math.pi * j / segs),
                       r * math.cos(phi) * math.sin(2 * math.pi * j / segs), r * math.sin(phi))
                      for j in range(segs)]
        verts.append((0, 0, r))
        top = len(verts) - 1
        faces = [(0, 1 + (j + 1) % segs, 1 + j) for j in range(segs)]
        for i in range(rings - 2):
            a, b = 1 + i * segs, 1 + (i + 1) * segs
            faces += [(a + j, a + (j + 1) % segs, b + (j + 1) % segs, b + j) for j in range(segs)]
        last = 1 + (rings - 2) * segs
        faces += [(last + j, last + (j + 1) % segs, top) for j in range(segs)]
        return self.mesh(name, verts, faces, mat, c, smooth=True)

    def torus(self, name, c, big, small, mat, segs=20, ring=6):
        verts = [((big + small * math.cos(2 * math.pi * k / ring)) * math.cos(2 * math.pi * j / segs),
                  (big + small * math.cos(2 * math.pi * k / ring)) * math.sin(2 * math.pi * j / segs),
                  small * math.sin(2 * math.pi * k / ring))
                 for j in range(segs) for k in range(ring)]
        faces = [(j * ring + k, ((j + 1) % segs) * ring + k, ((j + 1) % segs) * ring + (k + 1) % ring,
                  j * ring + (k + 1) % ring) for j in range(segs) for k in range(ring)]
        return self.mesh(name, verts, faces, mat, c, smooth=True)

    def tube(self, name, points, r, mat, segs=10, samples=24, r_end=None):
        """Swept tube through `points` (Catmull-Rom), radius tapering to r_end."""
        pts = [Vector(p) for p in points]
        path = []
        ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
        for i in range(1, len(ext) - 2):
            p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
            for s in range(samples):
                t = s / samples
                path.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                   + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        path.append(pts[-1])
        r_end = r if r_end is None else r_end
        verts, faces = [], []
        normal = Vector((0, 0, 1))
        for i, p in enumerate(path):
            tangent = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
            if abs(tangent.dot(normal)) > 0.95:
                normal = Vector((1, 0, 0))
            side = tangent.cross(normal).normalized()
            up = side.cross(tangent).normalized()
            rr = r + (r_end - r) * i / (len(path) - 1)
            verts += [p + rr * (math.cos(2 * math.pi * j / segs) * side + math.sin(2 * math.pi * j / segs) * up)
                      for j in range(segs)]
        for i in range(len(path) - 1):
            a, b = i * segs, (i + 1) * segs
            faces += [(a + j, a + (j + 1) % segs, b + (j + 1) % segs, b + j) for j in range(segs)]
        faces += [tuple(reversed(range(segs))), tuple(range((len(path) - 1) * segs, len(path) * segs))]
        return self.mesh(name, verts, faces, mat, smooth=True)


def mark_holdout(root) -> None:
    """Hide the base parts of an overlay render (they still occlude the overlay)."""
    stack = list(root.children)
    while stack:
        obj = stack.pop()
        stack.extend(obj.children)
        obj.is_holdout = True


def clear_subject(subject) -> None:
    stack, doomed = list(subject.children), []
    while stack:
        obj = stack.pop()
        stack.extend(obj.children)
        doomed.append(obj)
    for obj in doomed:
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)


# --------------------------------------------------------------------------- #
# Pipe work
# --------------------------------------------------------------------------- #

def _along(side, d, z=PIPE_Z):
    dx, dy = DIRS[side]
    return (dx * d, dy * d, z)


def arm(k: Kit, side, start=0.0, tag=""):
    """Galvanised pipe from `start` metres off the centre to the tile edge on `side`, ending in
    half a coupling: two neighbouring tiles draw one whole coupling on their shared edge."""
    axis = "x" if DIRS[side][0] else "y"
    length = 0.5 - start
    k.cyl(f"pipe{side}{tag}", _along(side, start + length / 2), PIPE_R, length, "galv", axis)
    k.cyl(f"coupling{side}{tag}", _along(side, 0.482), COUP_R, 0.036, "galv_dark", axis)


def fitting(k: Kit, sides, name="fitting"):
    """Malleable iron elbow / tee / cross at the centre: a hub and one short socket per side."""
    k.ball(f"{name}_hub", (0, 0, PIPE_Z), COUP_R * 1.02, "galv_dark", 12)
    for s in sides:
        k.cyl(f"{name}_socket{s}", _along(s, 0.045), COUP_R, 0.05, "galv_dark", "x" if DIRS[s][0] else "y")


def build_pipe(k: Kit, mask):
    sides = [s for s in (N, E, S, W) if mask & s]
    if not sides:
        # Loose nipple, capped both ends.
        k.cyl("pipe", (0, 0, PIPE_Z), PIPE_R, 0.34, "galv", "y")
        for y in (-0.18, 0.18):
            k.cyl(f"cap{y}", (0, y, PIPE_Z), COUP_R, 0.04, "galv_dark", "y")
        return
    for s in sides:
        arm(k, s)
    if len(sides) == 1:
        dx, dy = DIRS[sides[0]]
        k.cyl("cap", (0, 0, PIPE_Z), COUP_R, 0.04, "galv_dark", "x" if dx else "y")
    elif mask not in (N | S, E | W):
        fitting(k, sides)


# --------------------------------------------------------------------------- #
# Inline parts
# --------------------------------------------------------------------------- #

def build_valve(k: Kit, closed, along_x):
    """Brass gate valve with a red handwheel. Rising stem: open shows the threaded stem
    standing well above the wheel, closed leaves it flush."""
    a, b = (E, W) if along_x else (N, S)
    axis = "x" if along_x else "y"
    arm(k, a, start=0.09)
    arm(k, b, start=0.09)
    for s in (a, b):
        k.cyl(f"valve_hex{s}", _along(s, 0.075), 0.050, 0.035, "brass", axis, segs=6)
    k.cyl("valve_body", (0, 0, PIPE_Z), 0.058, 0.11, "brass", axis, segs=16)
    k.cyl("valve_bonnet", (0, 0, PIPE_Z + 0.08), 0.036, 0.10, "brass", segs=12)
    k.cyl("valve_nut", (0, 0, PIPE_Z + 0.135), 0.040, 0.026, "brass", segs=6)
    wheel_z = PIPE_Z + 0.175
    k.rod("valve_stem", (0, 0, PIPE_Z + 0.14), (0, 0, wheel_z + (0.014 if closed else 0.13)), 0.013, "brass", 8)
    if not closed:
        k.cyl("valve_stem_tip", (0, 0, wheel_z + 0.13), 0.016, 0.014, "galv_dark", segs=8)
    k.torus("valve_wheel", (0, 0, wheel_z), 0.068, 0.012, "red")
    for i in range(3):
        ang = 2 * math.pi * i / 3 + 0.4
        k.rod(f"valve_spoke{i}", (0, 0, wheel_z), (0.064 * math.cos(ang), 0.064 * math.sin(ang), wheel_z),
              0.008, "red", 6)
    k.cyl("valve_hub", (0, 0, wheel_z), 0.018, 0.024, "red", segs=8)


def build_flowmeter(k: Kit, along_x):
    """Bronze water meter: inline body with hex ends, round register on top, its hinged
    lid open over a white dial with a red sweep hand."""
    a, b = (E, W) if along_x else (N, S)
    axis = "x" if along_x else "y"
    arm(k, a, start=0.13)
    arm(k, b, start=0.13)
    k.cyl("meter_body", (0, 0, PIPE_Z + 0.01), 0.060, 0.20, "brass", axis, segs=16)
    for s in (a, b):
        k.cyl(f"meter_nut{s}", _along(s, 0.115), 0.048, 0.03, "brass", axis, segs=6)
    top = PIPE_Z + 0.115
    k.cyl("meter_register", (0, 0, top - 0.03), 0.078, 0.06, "brass", segs=24)
    k.cyl("meter_dial", (0, 0, top + 0.001), 0.062, 0.004, "dial", segs=24)
    k.box("meter_hand", (0.018, -0.012, top + 0.005), (0.05, 0.008, 0.004), "needle", (0, 0, 0.7))
    k.box("meter_wheels", (0, 0.025, top + 0.004), (0.05, 0.016, 0.004), "rubber")
    tilt = math.radians(20)
    k.cyl("meter_lid", (0, 0.078 + 0.078 * math.sin(tilt), top + 0.078 * math.cos(tilt)), 0.078, 0.012,
          "brass", segs=24, rot=(math.pi / 2 - tilt, 0, 0))


# --------------------------------------------------------------------------- #
# Pump: electric centrifugal pump on a wooden skid
# --------------------------------------------------------------------------- #

PUMP_AXIS_Z = 0.235
PUMP_LAMP = (0.24, 0.0, PUMP_AXIS_Z + 0.215)


def build_pump(k: Kit, with_filter=False):
    """Suction hose over the S edge into the water, discharge to the N edge."""
    for y in (-0.12, 0.12):
        k.box(f"skid{y}", (0.15, y, 0.03), (0.66, 0.07, 0.06), "wood")
    k.box("base_plate", (0.16, 0, 0.07), (0.58, 0.32, 0.02), "iron")
    z = PUMP_AXIS_Z
    # Motor, axis along X, with cooling ribs, feet, end bell and terminal box.
    k.cyl("motor", (0.25, 0, z), 0.12, 0.32, "motor", "x", 24)
    for i in range(5):
        k.cyl(f"motor_rib{i}", (0.13 + 0.06 * i, 0, z), 0.128, 0.012, "motor", "x", 24)
    k.cyl("motor_bell", (0.425, 0, z), 0.105, 0.04, "motor", "x", 24)
    k.cyl("motor_shaft_cap", (0.452, 0, z), 0.035, 0.02, "iron", "x", 12)
    for x in (0.15, 0.35):
        k.box(f"motor_foot{x}", (x, 0, 0.115), (0.05, 0.22, 0.07), "motor")
    k.box("terminal_box", (0.24, 0, z + 0.15), (0.13, 0.11, 0.08), "motor")
    k.cyl("terminal_lamp_ring", (PUMP_LAMP[0], PUMP_LAMP[1], PUMP_LAMP[2] - 0.012), 0.026, 0.012, "iron", segs=12)
    k.cyl("terminal_lamp", (PUMP_LAMP[0], PUMP_LAMP[1], PUMP_LAMP[2]), 0.02, 0.016, "lamp", segs=12)
    k.tube("power_cord", [(0.30, 0.055, z + 0.15), (0.36, 0.20, z + 0.10), (0.40, 0.36, 0.04),
                          (0.42, 0.50, 0.015)], 0.011, "rubber", 8)
    # Cast iron pump: adapter, volute, axial suction, tangential discharge on top.
    k.cyl("adapter", (0.065, 0, z), 0.075, 0.05, "iron", "x", 16)
    k.cyl("volute", (0.0, 0, z), 0.135, 0.09, "iron", "x", 24)
    k.box("volute_foot", (0.0, 0, 0.11), (0.07, 0.16, 0.06), "iron")
    k.cyl("suction_port", (-0.075, 0, z), 0.048, 0.06, "iron", "x", 12)
    k.cyl("drain_plug", (0.0, -0.08, z - 0.10), 0.012, 0.02, "brass", "y", 6)
    # Suction hose (black, ribbed look from rings) to a foot valve in the water.
    k.tube("suction_hose", [(-0.10, 0, z), (-0.20, -0.06, z - 0.03), (-0.18, -0.30, 0.07),
                            (-0.12, -0.52, 0.02), (-0.10, -0.62, -0.02)], 0.030, "rubber", 12)
    k.cyl("hose_clamp", (-0.11, 0, z), 0.036, 0.016, "galv", "x", 12)
    k.cyl("foot_valve", (-0.10, -0.64, -0.01), 0.04, 0.07, "brass", "y", 12)
    # Discharge: up off the volute, along +Y, down to pipe height, out over the N edge.
    top = z + 0.135
    k.cyl("discharge_nipple", (0, 0.035, top - 0.01), PIPE_R, 0.06, "galv", segs=12)
    k.ball("discharge_elbow", (0, 0.035, top + 0.03), COUP_R, "galv_dark")
    k.cyl("discharge_run", (0, 0.22, top + 0.03), PIPE_R, 0.33, "galv", "y")
    k.ball("discharge_elbow2", (0, 0.40, top + 0.03), COUP_R, "galv_dark")
    k.cyl("discharge_drop", (0, 0.40, (top + 0.03 + PIPE_Z) / 2), PIPE_R, top + 0.03 - PIPE_Z, "galv")
    k.ball("discharge_elbow3", (0, 0.40, PIPE_Z), COUP_R, "galv_dark")
    arm(k, N, start=0.40, tag="_out")
    if with_filter:
        fz = top + 0.03
        k.box("filter_head", (0, 0.24, fz - 0.005), (0.11, 0.09, 0.05), "iron")
        k.cyl("filter_ring", (0, 0.24, fz - 0.045), 0.068, 0.03, "iron", segs=16)
        k.cyl("filter_bowl", (0, 0.24, fz - 0.15), 0.06, 0.19, "bowl", segs=16, r2=0.062)


def build_pump_lit(k: Kit, with_filter=False):
    build_pump(k, with_filter)
    mark_holdout(k.anchor)
    return [k.cyl("terminal_lamp_on", (PUMP_LAMP[0], PUMP_LAMP[1], PUMP_LAMP[2] + 0.001), 0.021, 0.017,
                  "lit_green", segs=12)]


# --------------------------------------------------------------------------- #
# House inlet: wall-mounted box against the N wall
# --------------------------------------------------------------------------- #

INLET_Y = WALL_Y - 0.075
INLET_LAMP = (0.07, INLET_Y - 0.052, 0.66)


def build_house_inlet(k: Kit):
    """Feed pipe over the S edge, riser with a brass hose bib, steel box, pipe into the wall."""
    k.box("backboard", (0, WALL_Y - 0.01, 0.52), (0.36, 0.02, 0.62), "board")
    py = INLET_Y - 0.03
    k.cyl("feed", (0, (-0.5 + py) / 2, PIPE_Z), PIPE_R, 0.5 + py, "galv", "y")
    k.cyl("feed_coupling", (0, -0.482, PIPE_Z), COUP_R, 0.036, "galv_dark", "y")
    k.ball("feed_elbow", (0, py, PIPE_Z), COUP_R, "galv_dark")
    k.cyl("riser", (0, py, (PIPE_Z + 0.50) / 2), PIPE_R, 0.50 - PIPE_Z, "galv")
    k.cyl("bib_tee", (0, py, 0.30), COUP_R, 0.07, "galv_dark")
    k.cyl("bib_body", (0, py - 0.06, 0.30), 0.03, 0.09, "brass", "y", 12)
    k.cyl("bib_spout", (0, py - 0.10, 0.275), 0.018, 0.05, "brass", segs=10)
    k.torus("bib_wheel", (0, py - 0.065, 0.355), 0.03, 0.007, "red", 12, 5)
    k.rod("bib_stem", (0, py - 0.065, 0.33), (0, py - 0.065, 0.36), 0.006, "brass", 6)
    # Box: valve and pressure switch housing, gauge and status lamp on the door.
    k.box("inlet_box", (0, INLET_Y, 0.64), (0.26, 0.10, 0.30), "box")
    k.box("inlet_latch", (0.10, INLET_Y - 0.054, 0.62), (0.014, 0.008, 0.04), "iron")
    k.cyl("gauge_case", (-0.05, INLET_Y - 0.055, 0.68), 0.045, 0.014, "iron", "y", 16)
    k.cyl("gauge_face", (-0.05, INLET_Y - 0.0625, 0.68), 0.037, 0.002, "dial", "y", 16)
    k.box("gauge_hand", (-0.04, INLET_Y - 0.065, 0.69), (0.026, 0.002, 0.005), "needle", (0, -0.6, 0))
    k.cyl("lamp_ring", (INLET_LAMP[0], INLET_LAMP[1] + 0.004, INLET_LAMP[2]), 0.024, 0.01, "iron", "y", 12)
    k.cyl("lamp", INLET_LAMP, 0.018, 0.008, "lamp", "y", 12)
    k.cyl("to_wall_nipple", (0, py, 0.83), PIPE_R, 0.08, "galv")
    k.ball("to_wall_elbow", (0, py, 0.87), COUP_R, "galv_dark")
    k.cyl("to_wall", (0, (py + 0.5) / 2, 0.87), PIPE_R, 0.5 - py, "galv", "y")


def build_house_inlet_lit(colour):
    def fn(k: Kit):
        build_house_inlet(k)
        mark_holdout(k.anchor)
        return [k.cyl("lamp_on", (INLET_LAMP[0], INLET_LAMP[1] - 0.0015, INLET_LAMP[2]), 0.019, 0.006,
                      f"lit_{colour}", "y", 12)]
    return fn


# --------------------------------------------------------------------------- #
# Impact sprinkler on a riser
# --------------------------------------------------------------------------- #

SPR_TOP = 0.46


def build_sprinkler(k: Kit, active, automatic):
    """Fed over the S edge: ball valve (manual) or hose timer (automatic) on the feed,
    elbow up, 1/2 in riser tied to a stake, brass impact head."""
    arm(k, S, start=0.0)
    k.ball("elbow", (0, 0, PIPE_Z), COUP_R, "galv_dark")
    k.cyl("riser", (0, 0, (PIPE_Z + SPR_TOP) / 2), 0.022, SPR_TOP - PIPE_Z, "galv", segs=10)
    k.box("stake", (0.05, 0.035, 0.23), (0.032, 0.032, 0.46), "wood")
    for zt in (0.16, 0.36):
        k.cyl(f"tie{zt}", (0.025, 0.017, zt), 0.042, 0.012, "iron", segs=10)
    vy = -0.22
    if automatic:
        k.box("timer", (0, vy, PIPE_Z + 0.025), (0.12, 0.10, 0.11), "plastic")
        k.cyl("timer_dial", (0, vy, PIPE_Z + 0.085), 0.038, 0.014, "dial", segs=16)
        k.box("timer_mark", (0.012, vy - 0.01, PIPE_Z + 0.093), (0.03, 0.006, 0.004), "rubber",
              (0, 0, -0.9 if active else 0.5))
    else:
        k.cyl("valve_body", (0, vy, PIPE_Z), 0.045, 0.09, "brass", "y", 12)
        k.cyl("valve_stem", (0, vy, PIPE_Z + 0.05), 0.012, 0.03, "brass", segs=8)
        # Quarter-turn lever: along the pipe when open, across when closed.
        size = (0.018, 0.12, 0.012) if active else (0.12, 0.018, 0.012)
        off = (0, -0.05, 0) if active else (0.05, 0, 0)
        k.box("valve_lever", (off[0], vy + off[1], PIPE_Z + 0.068), size, "red")
    # Impact head: bearing, body, angled nozzle, swinging arm with spoon and counterweight.
    d = Vector((-1.0, -0.5, 0.0)).normalized()
    k.cyl("head_bearing", (0, 0, SPR_TOP + 0.015), 0.026, 0.03, "brass", segs=12)
    k.cyl("head_body", (0, 0, SPR_TOP + 0.045), 0.022, 0.035, "brass", segs=10)
    tip = Vector((0, 0, SPR_TOP + 0.05)) + d * 0.085 + Vector((0, 0, 0.035))
    k.rod("head_nozzle", (0, 0, SPR_TOP + 0.05), tuple(tip), 0.011, "brass", 8)
    pivot = Vector((0, 0, SPR_TOP + 0.10))
    k.rod("head_pin", (0, 0, SPR_TOP + 0.06), tuple(pivot), 0.005, "galv", 6)
    k.rod("head_arm", tuple(pivot - d * 0.06), tuple(pivot + d * 0.09), 0.007, "brass", 6)
    k.box("head_spoon", tuple(pivot + d * 0.095 + Vector((0, 0, -0.015))), (0.025, 0.025, 0.02), "brass")
    k.box("head_weight", tuple(pivot - d * 0.07), (0.03, 0.03, 0.03), "brass")
    k.cyl("head_spring", tuple(pivot + Vector((0, 0, 0.012))), 0.012, 0.018, "galv", segs=8)
    return tip, d


JET_FRAMES = 6
#: Part-circle sweep of the impact head, degrees each side of the nozzle direction.
JET_SWEEP = 36.0


def jet_parts(k: Kit, tip, d, frame):
    """Water of one animation frame. The jet steps across the sweep (one tick per frame,
    then the fast return of a part-circle impact sprinkler); on odd frames the arm's spoon
    is in the stream: the jet is cut short and bursts into spray near the nozzle."""
    ang = math.radians(-JET_SWEEP + 2 * JET_SWEEP * frame / (JET_FRAMES - 1))
    d = Vector((d.x * math.cos(ang) - d.y * math.sin(ang), d.x * math.sin(ang) + d.y * math.cos(ang), 0))
    side = Vector((-d.y, d.x, 0))
    struck = frame % 2 == 1
    reach = 0.26 if struck else 0.40

    def arc(t):
        return tip + d * (reach * t) + Vector((0, 0, 0.16 * t - 0.30 * t * t))

    parts = [k.tube("jet", [tuple(arc(t)) for t in (0, 0.25, 0.5, 0.75, 1.0)], 0.011, "water_jet", 8, 10,
                    r_end=0.006)]
    if struck:
        # Spoon strike: a short fan of spray out of the side of the nozzle.
        for i, (u, s_, z) in enumerate(((0.10, 0.10, 0.02), (0.14, 0.05, -0.04), (0.12, -0.06, 0.0),
                                        (0.08, 0.13, -0.08), (0.16, 0.0, -0.10))):
            a_ = tip + d * 0.03
            b_ = tip + d * u + side * s_ + Vector((0, 0, z))
            parts.append(k.tube(f"burst{i}", [tuple(a_), tuple((a_ + b_) / 2 + Vector((0, 0, 0.02))), tuple(b_)],
                                0.005, "water_mist", 6, 5, r_end=0.002))
    end = arc(1.0)
    strands = ((0.70, -0.03, 0.5), (0.80, 0.04, 0.8), (0.90, -0.05, 0.6), (0.98, 0.02, 1.0),
               (1.05, -0.02, 0.9), (1.10, 0.05, 0.7))
    for i, (t, s_, fall) in enumerate(strands):
        a_ = arc(min(t, 1.0)) + d * (reach * max(0.0, t - 1.0)) + side * (s_ * (1 + 0.5 * (frame % 3)))
        b_ = a_ + d * 0.05 + side * (s_ * 0.6) + Vector((0, 0, -(a_.z - 0.02) * fall))
        parts.append(k.tube(f"strand{i}", [tuple(a_), tuple((a_ + b_) / 2 + d * 0.02), tuple(b_)],
                            0.005, "water_mist", 6, 6, r_end=0.003))
    # Drops at heights that change every frame, so the falling water flickers when cycled.
    for i in range(4):
        t = 0.75 + 0.12 * i
        z = 0.04 + ((frame * 0.07 + i * 0.13) % 0.22)
        p = end + d * (reach * (t - 0.9)) + side * (0.07 * (1 if i % 2 else -1))
        p = Vector((p.x, p.y, z))
        parts.append(k.tube(f"drop{i}", [tuple(p), tuple(p + Vector((0, 0, -0.03)))], 0.005,
                            "water_jet", 6, 2, r_end=0.003))
    return parts


def build_jet(frame):
    """Jet overlay frame: the sprinkler is a holdout (it hides the water behind it) and draws nothing."""
    def fn(k: Kit):
        tip, d = build_sprinkler(k, True, False)
        mark_holdout(k.anchor)
        return jet_parts(k, tip, d, frame)
    return fn


# --------------------------------------------------------------------------- #
# Barrel fitting: brass valve, garden hose into the rain barrel on the N tile
# --------------------------------------------------------------------------- #

#: Rim of the rain collector on the N tile, measured on vanilla sprites (same cell framing):
#: round barrels (carpentry_02_122-126, industry_01_23, location_military_generic_01_7) are about
#: 0.82 m across with their rim near 0.78 m; the tarp crates (carpentry_02_52/54/120) are 1 m wide
#: with their rim near 0.60 m. (front of the rim y, rim height z)
RIM = {"tall": (0.59, 0.80), "low": (0.50, 0.62)}


def build_barrel_connector(k: Kit, mode, rim="tall"):
    """Fill: the hose hooks over the rim of the collector on the N tile and pours in. Pump: the
    hose screws onto the spigot at the foot of the collector and draws from it."""
    arm(k, S, start=0.06)
    k.cyl("valve_body", (0, 0, PIPE_Z), 0.045, 0.10, "brass", "y", 12)
    k.cyl("valve_stem", (0, 0, PIPE_Z + 0.05), 0.012, 0.03, "brass", segs=8)
    k.box("valve_lever", (0, -0.05, PIPE_Z + 0.068), (0.018, 0.12, 0.012), "red")
    k.cyl("hose_barb", (0, 0.07, PIPE_Z), 0.022, 0.05, "brass", "y", 10)
    k.cyl("hose_collar", (0, 0.10, PIPE_Z), 0.03, 0.025, "galv", "y", 10)
    if mode == "fill":
        fy, fz = RIM[rim]
        path = [(0, 0.11, PIPE_Z), (0.02, 0.24, 0.07), (0.03, fy - 0.14, fz * 0.45), (0.02, fy - 0.04, fz - 0.02),
                (0.0, fy + 0.02, fz + 0.07), (0.0, fy + 0.08, fz + 0.03)]
        k.tube("hose", path, 0.024, "hose", 10)
        k.cyl("nozzle", (0, fy + 0.09, fz - 0.01), 0.026, 0.06, "brass", segs=10)
    else:
        path = [(0, 0.11, PIPE_Z), (0.03, 0.30, 0.04), (0.02, 0.48, 0.06), (0.0, 0.58, 0.10)]
        k.tube("hose", path, 0.024, "hose", 10)
        k.cyl("spigot_nut", (0, 0.60, 0.10), 0.03, 0.04, "brass", "y", 10)
        k.cyl("spigot", (0, 0.645, 0.10), 0.02, 0.05, "brass", "y", 10)


# --------------------------------------------------------------------------- #
# Inventory items
# --------------------------------------------------------------------------- #

def build_item_pipe(k: Kit):
    k.cyl("pipe", (0, 0, 0.05), 0.05, 0.86, "galv", "x", 20)
    for x in (-0.405, 0.405):
        for i in range(3):
            k.cyl(f"thread{x}{i}", (x + (0.012 * i if x < 0 else -0.012 * i), 0, 0.05), 0.052, 0.006,
                  "galv_dark", "x", 20)
    k.cyl("coupling", (0.45, 0, 0.05), 0.064, 0.09, "galv_dark", "x", 20)


def build_item_filter(k: Kit):
    """Pleated paper cartridge between black end caps."""
    k.cyl("core", (0, 0, 0.25), 0.13, 0.40, "paper", segs=24)
    for i in range(20):
        ang = 2 * math.pi * i / 20
        k.box(f"pleat{i}", (0.135 * math.cos(ang), 0.135 * math.sin(ang), 0.25), (0.03, 0.012, 0.40), "paper",
              (0, 0, ang))
    for z in (0.035, 0.465):
        k.cyl(f"cap{z}", (0, 0, z), 0.165, 0.035, "rubber", segs=32)
    k.cyl("hole", (0, 0, 0.484), 0.05, 0.004, "iron", segs=20)


ITEMS = [("pipe_section", build_item_pipe, (0, 0, 0.05), 2.2),
         ("water_filter", build_item_filter, (0, 0, 0.25), 1.6)]


# --------------------------------------------------------------------------- #
# Groups: sprite base name, facings, builder, optional overlay (lights, water)
# --------------------------------------------------------------------------- #

def tile_groups() -> list[dict]:
    """Every render group, indexed by the tile contract (docs/annexes/conception/tuiles-contrat.md).

    `indices`: sprite index of each facing, in forge order S, E[, N, W]. `lit` builds a light
    overlay (base as holdout) composited onto the styled base, its pixels pushed toward the
    `glow` colour. `overlay` groups are sprites of their own drawn over another tile (the
    animated sprinkler jet): not styled, kept as rendered."""
    def g(key, first, build, lit=None, glow=None, facings=4, overlay=False):
        return {"key": key, "indices": list(range(first, first + facings)), "build": build, "lit": lit,
                "glow": glow, "overlay": overlay}

    green, amber = (70, 255, 90), (255, 170, 30)
    groups = [g(f"pipe_m{m:02d}", m, (lambda m: lambda k: build_pipe(k, m))(m), facings=1) for m in range(16)]
    groups += [
        g("valve_open_ew", 16, lambda k: build_valve(k, False, True), facings=1),
        g("valve_open_ns", 17, lambda k: build_valve(k, False, False), facings=1),
        g("valve_closed_ew", 18, lambda k: build_valve(k, True, True), facings=1),
        g("valve_closed_ns", 19, lambda k: build_valve(k, True, False), facings=1),
        g("flowmeter_ew", 20, lambda k: build_flowmeter(k, True), facings=1),
        g("flowmeter_ns", 21, lambda k: build_flowmeter(k, False), facings=1),
        g("pump_off", 24, lambda k: build_pump(k)),
        g("pump_on", 28, lambda k: build_pump(k), lambda k: build_pump_lit(k), green),
        g("pump_filter_on", 32, lambda k: build_pump(k, True), lambda k: build_pump_lit(k, True), green),
        g("pump_filter_off", 36, lambda k: build_pump(k, True)),
        g("house_inlet", 40, build_house_inlet, build_house_inlet_lit("green"), green),
        g("house_inlet_unfiltered", 44, build_house_inlet, build_house_inlet_lit("amber"), amber),
        g("sprinkler_manual_off", 48, lambda k: build_sprinkler(k, False, False)),
        g("sprinkler_manual_on", 52, lambda k: build_sprinkler(k, True, False)),
        g("sprinkler_auto_off", 56, lambda k: build_sprinkler(k, False, True)),
        g("sprinkler_auto_on", 60, lambda k: build_sprinkler(k, True, True)),
        g("barrel_fill", 64, lambda k: build_barrel_connector(k, "fill", "tall")),
        g("barrel_fill_low", 68, lambda k: build_barrel_connector(k, "fill", "low")),
        g("barrel_pump", 72, lambda k: build_barrel_connector(k, "pump")),
    ]
    groups += [g(f"sprinkler_jet{f}", 80 + 4 * f, build_jet(f), overlay=True) for f in range(JET_FRAMES)]
    return groups


def build_group(subject, mats, group) -> list:
    """Clear the subject and build one group; returns the names of the parts the sprite draws
    when it is an overlay (build_depthmap.py contract), else an empty list."""
    clear_subject(subject)
    parts = group["build"](Kit(subject, mats)) or []
    if not group["overlay"]:
        return []
    return sorted(obj.name for obj in parts)


def lit_key(key: str) -> str:
    return f"{key}__lit"


def build(subject, mats) -> None:
    """Showcase of every part in a row (editable .blend, depth tools)."""
    k = Kit(subject, mats)
    for i, group in enumerate(g for g in tile_groups()[16:] if not g["overlay"]):
        group["build"](k.empty(f"show_{group['key']}", (i * 1.2, 0, 0)))


# --------------------------------------------------------------------------- #
# Rendering (Blender)
# --------------------------------------------------------------------------- #

def render_group(props, subject, mats, key, facings, fn, out: Path):
    clear_subject(subject)
    fn(Kit(subject, mats))
    props.sheet_name = key
    props.facings = facings
    props.output_dir = str(out / "cells" / key)
    manifest = F.render_cells(bpy.context)
    print(f"rendered {key}: {len(manifest['cells'])} cells")


def render_items(scene, subject, mats, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cam = bpy.data.objects.new("LWT_ItemCam", bpy.data.cameras.new("LWT_ItemCam"))
    scene.collection.objects.link(cam)
    cam.data.lens = 60
    saved = (scene.camera, scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath)
    try:
        scene.camera = cam
        scene.render.resolution_x = scene.render.resolution_y = 256
        for name, fn, target, dist in ITEMS:
            clear_subject(subject)
            fn(Kit(subject, mats))
            t = Vector(target)
            cam.location = t + Vector((0.9, -1.4, 0.9)).normalized() * dist
            cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(out_dir / f"{name}.png")
            bpy.ops.render.render(write_still=True)
    finally:
        scene.camera, scene.render.resolution_x, scene.render.resolution_y, scene.render.filepath = saved


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(args[0] if args else "build/livewater_tiles")
    only = set(args[1:])
    if not bpy.app.background:
        raise SystemExit("render headless only (the forge rig names are global)")
    scene = bpy.context.scene
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    F.register()
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.footprint_x = props.footprint_y = 1
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True
    F.build_rig(bpy.context)
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    subject = bpy.data.objects[F.SUBJECT_NAME]
    out.mkdir(parents=True, exist_ok=True)
    mats = materials(out)
    for group in tile_groups():
        if only and group["key"] not in only:
            continue
        facings = str(len(group["indices"]))
        render_group(props, subject, mats, group["key"], facings, group["build"], out)
        if group["lit"]:
            render_group(props, subject, mats, lit_key(group["key"]), facings, group["lit"], out)
    if not only or "items" in only:
        render_items(scene, subject, mats, out / "items")
    clear_subject(subject)
    print("done")


# --------------------------------------------------------------------------- #
# Style step (plain Python with Pillow + pzforge)
# --------------------------------------------------------------------------- #

#: Throwaway tiledef id for the style build: nothing is packed into the mod (D23).
STYLE_TILEDEF_ID = 8000


def manifest_cells(group_dir: Path) -> list[dict]:
    return json.loads((group_dir / "manifest.json").read_text())["cells"]


def styled_cells(group_dir: Path, work: Path) -> list:
    """Run the pzforge style pass on one group; return its styled cells in manifest order."""
    from PIL import Image
    from pzforge import cli
    dist = work / group_dir.name
    args = ["build", str(group_dir), "--out", str(dist), "--mod-id", "lwt",
            "--tiledef-id", str(STYLE_TILEDEF_ID)]
    if cli.main(args) != 0:
        raise RuntimeError(f"pzforge build failed for {group_dir}")
    sheet = Image.open(next(dist.rglob(f"{group_dir.name}.png"))).convert("RGBA")
    count = len(manifest_cells(group_dir))
    return [sheet.crop(((i % 8) * 128, (i // 8) * 256, (i % 8) * 128 + 128, (i // 8) * 256 + 256))
            for i in range(count)]


def overlay_cells(group_dir: Path, glow) -> list:
    """Raw overlay renders (lit lamps pushed toward their light colour, water as rendered)."""
    from PIL import Image
    cells = [Image.open(group_dir / c["file"]).convert("RGBA") for c in manifest_cells(group_dir)]
    return [light_up(c, glow) for c in cells] if glow else cells


def light_up(img, colour):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (int(0.25 * r + 0.75 * colour[0]), int(0.25 * g + 0.75 * colour[1]),
                            int(0.25 * b + 0.75 * colour[2]), a)
    return img


def outline_icon(img):
    """Inventory icon: crop, dark 1 px contour like vanilla icons, fit into 64 x 64."""
    from PIL import Image, ImageFilter
    img = img.crop(img.getbbox())
    side = max(img.size) + 8
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    small = sq.resize((64, 64), Image.LANCZOS)
    alpha = small.getchannel("A").point(lambda a: 255 if a > 90 else 0)
    ring = alpha.filter(ImageFilter.MaxFilter(3))
    contour = Image.new("RGBA", small.size, (28, 24, 20, 255))
    contour.putalpha(ring)
    contour.alpha_composite(small)
    return contour


def style(out: Path, only=()) -> None:
    from PIL import Image
    cells_dir, work = out / "cells", out / "_dist"
    target = out / "styled"
    target.mkdir(parents=True, exist_ok=True)
    for group in tile_groups():
        key = group["key"]
        if only and key not in only:
            continue
        if not (cells_dir / key / "manifest.json").exists():
            raise SystemExit(f"group not rendered: {key}")
        facings = [c["facing"] for c in manifest_cells(cells_dir / key)]
        if group["overlay"]:
            images = overlay_cells(cells_dir / key, None)
        else:
            images = styled_cells(cells_dir / key, work)
        if group["lit"]:
            for img, over in zip(images, overlay_cells(cells_dir / lit_key(key), group["glow"])):
                img.alpha_composite(over)
        for facing, img in zip(facings, images):
            img.save(target / f"{key}_{facing}.png")
    items = out / "styled_items"
    items.mkdir(parents=True, exist_ok=True)
    for name, *_ in ITEMS:
        outline_icon(Image.open(out / "items" / f"{name}.png").convert("RGBA")).save(items / f"{name}.png")
    print(f"styled into {target} and {items}")


# --------------------------------------------------------------------------- #
# Packaging (plain Python with Pillow + pzforge): tileset of the tile contract
# --------------------------------------------------------------------------- #

SHEET = "batman_livewater_01"
TILEDEF_ID = 7176
MOD_ID = "batman_LiveWater"
TOTAL = 104
FACING_NAMES = ["S", "E", "N", "W"]
#: Plumbing parts are taken up and set down with a pipe wrench, like vanilla sinks.
_TOOLS = {"PickUpTool": "Wrench", "PlaceTool": "Wrench"}
_GROUP = {"GroupName": "Live Water"}


def _moveable(name, item, weight, **extra):
    return {**_GROUP, "CustomName": name, "IsMoveAble": "", "Material": "MetalPlates", "PickUpWeight": str(weight),
            "CustomItem": f"Base.Mov_LiveWater_{item}", **_TOOLS, **extra}


#: (first index, count, faces, properties). faces 4: S E N W; 2: the ew / ns pair of an inline
#: part (ew drawn as Facing E, ns as Facing S); 1: no rotation (pipes, laid by a build action).
#: Overlays (80-103) and reserved indices get no properties.
KINDS = [(m, 1, 1, {**_GROUP, "CustomName": "Water Pipe", "Material": "MetalPlates"}) for m in range(16)] + [
    (16, 2, 2, _moveable("Shut-off Valve", "Valve", 30)),
    (18, 2, 2, _moveable("Shut-off Valve", "Valve", 30)),
    (20, 2, 2, _moveable("Water Meter", "FlowMeter", 40)),
] + [(b, 4, 4, _moveable("Pond Pump", "PondPump", 150, solidtrans="", BlocksPlacement=""))
     for b in (24, 28, 32, 36)] + [
    (b, 4, 4, _moveable("House Water Inlet", "HouseInlet", 60, BlocksPlacement="")) for b in (40, 44)] + [
    (b, 4, 4, _moveable("Sprinkler", "Sprinkler", 30, BlocksPlacement="")) for b in (48, 52)] + [
    (b, 4, 4, _moveable("Automatic Sprinkler", "SprinklerAuto", 35, BlocksPlacement="")) for b in (56, 60)] + [
    (b, 4, 4, _moveable("Barrel Fitting", "BarrelFitting", 15)) for b in (64, 68, 72)]

#: Face offsets toward the sister sprites (rotation while placing: ISMoveableSpriteProps).
_OFFSETS = {4: [{"Eoffset": 1, "Noffset": 2, "Woffset": 3}, {"Soffset": -1, "Noffset": 1, "Woffset": 2},
                {"Soffset": -2, "Eoffset": -1, "Woffset": 1}, {"Soffset": -3, "Eoffset": -2, "Noffset": -1}],
            2: [{"Soffset": 1}, {"Eoffset": -1}]}


def tile_props(i: int) -> dict:
    for first, count, faces, props in KINDS:
        if first <= i < first + count:
            k = i - first
            if faces == 1:
                return dict(props)
            facing = FACING_NAMES[k] if faces == 4 else ("E", "S")[k]
            return {**props, "Facing": facing, **{key: str(v) for key, v in _OFFSETS[faces][k].items()}}
    return {}


def check_tiledef_free(tiledef_id: int) -> None:
    from pzforge.modgen import used_tiledef_ids
    roots = [Path("D:/SteamLibrary/steamapps/workshop/content/108600"), Path.home() / "Zomboid" / "mods",
             Path.home() / "Zomboid" / "Workshop"]
    owners = [o for o in used_tiledef_ids([r for r in roots if r.exists()]).get(tiledef_id, []) if SHEET not in o]
    if owners:
        raise SystemExit(f"tiledef {tiledef_id} already used by {owners}")


def package(out: Path, project: Path) -> None:
    """Styled cells -> <mod>/common/media: .pack, .tiles, tileGeometry.txt; icons -> 42.21/media/textures."""
    from PIL import Image
    from pzforge.sheet import Cell, Sheet, pack_sheet
    from pzforge.tiledef import TileDefinitions, Tile, Tileset

    check_tiledef_free(TILEDEF_ID)
    images = {}
    for group in tile_groups():
        for facing_index, index in enumerate(group["indices"]):
            path = out / "styled" / f"{group['key']}_{FACING_NAMES[facing_index]}.png"
            if not path.exists():
                raise SystemExit(f"not styled: {path.name}")
            images[index] = Image.open(path).convert("RGBA")
    blank = Image.new("RGBA", (128, 256), (0, 0, 0, 0))
    sheet = Sheet(SHEET, 128, 256, 8, [Cell(images.get(i, blank), index=i) for i in range(TOTAL)])
    tiles = [Tile(tile_props(i)) for i in range(TOTAL)]
    tdefs = TileDefinitions([Tileset(SHEET, f"{SHEET}.png", 8, TOTAL // 8, 1, tiles)])
    mod = project / "Contents" / "mods" / MOD_ID
    media = mod / "common" / "media"
    (media / "texturepacks").mkdir(parents=True, exist_ok=True)
    pack_sheet(sheet).write(media / "texturepacks" / f"{SHEET}.pack")
    tdefs.write(media / f"{SHEET}.tiles")
    (media / "tileGeometry.txt").write_text("tileGeometry\n{\n    VERSION = 2,\n}\n", encoding="ascii")
    (out / f"{SHEET}.tiles.txt").write_text(tdefs.to_text(), encoding="ascii")
    sheet.image().save(out / f"{SHEET}_sheet.png")
    textures = mod / "42.21" / "media" / "textures"
    textures.mkdir(parents=True, exist_ok=True)
    for name, icon in (("pipe_section", "Item_LWT_PipeSection"), ("water_filter", "Item_LWT_WaterFilter")):
        Image.open(out / "styled_items" / f"{name}.png").convert("RGBA").save(textures / f"{icon}.png")
    print(f"packed {len(images)} sprites into {media} (tiledef {TILEDEF_ID})")


USAGE = ("usage: python build_livewater_tiles.py style <out-dir> [<key>...]\n"
         "       python build_livewater_tiles.py package <out-dir> <project-root>")

if __name__ == "__main__":
    if bpy is None:
        if len(sys.argv) >= 3 and sys.argv[1] == "style":
            style(Path(sys.argv[2]), set(sys.argv[3:]))
        elif len(sys.argv) == 4 and sys.argv[1] == "package":
            package(Path(sys.argv[2]), Path(sys.argv[3]))
        else:
            raise SystemExit(USAGE)
    else:
        main()
