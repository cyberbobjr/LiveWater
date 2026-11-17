"""Provisional tiles of LiveWater, for the D23 presentation board (plan step E06).

They show what each part looks like and how it connects. Nothing here is packed
into the mod before the user's validation (ADR-001 D23): no .pack, no .tiles.

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
3. Board and example scene: tools/make_tile_board.py, tools/make_network_scene.py.

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
        k.box("timer_mark", (0.012, vy - 0.01, PIPE_Z + 0.093), (0.03, 0.006, 0.004), "rubber", (0, 0, 0.5))
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


def build_sprinkler_lit(automatic):
    """Water overlay: one jet arcing out of the nozzle, breaking into a falling curtain."""
    def fn(k: Kit):
        tip, d = build_sprinkler(k, True, automatic)
        mark_holdout(k.anchor)
        side = Vector((-d.y, d.x, 0))
        reach = 0.40
        jet = [tip + d * (reach * t) + Vector((0, 0, 0.16 * t - 0.30 * t * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        parts = [k.tube("jet", [tuple(p) for p in jet], 0.011, "water_jet", 8, 10, r_end=0.006)]
        end = jet[-1]
        # Break-up: thin translucent strands falling from the end of the arc, a few drops.
        strands = ((0.70, -0.03, 0.5), (0.78, 0.04, 0.8), (0.86, -0.05, 0.6), (0.92, 0.02, 1.0),
                   (0.98, -0.02, 0.9), (1.04, 0.05, 0.7), (1.08, -0.04, 1.0), (1.12, 0.01, 0.8))
        for i, (t, s_, fall) in enumerate(strands):
            a_ = tip + d * (reach * min(t, 1.0)) + Vector((0, 0, 0.16 * min(t, 1) - 0.30 * min(t, 1) ** 2))
            a_ = a_ + d * (reach * max(0.0, t - 1.0)) + side * s_
            b_ = a_ + d * 0.05 + side * (s_ * 0.6) + Vector((0, 0, -(a_.z - 0.02) * fall))
            parts.append(k.tube(f"strand{i}", [tuple(a_), tuple((a_ + b_) / 2 + d * 0.02), tuple(b_)],
                                0.005, "water_mist", 6, 6, r_end=0.003))
        for i, (t, s_, z) in enumerate(((0.9, 0.08, 0.10), (1.05, -0.08, 0.05), (1.15, 0.06, 0.16),
                                        (0.8, -0.06, 0.18))):
            p = tip + d * (reach * t) + side * s_
            p = Vector((p.x, p.y, z))
            parts.append(k.tube(f"drop{i}", [tuple(p), tuple(p + Vector((0, 0, -0.03)))], 0.005,
                                "water_jet", 6, 2, r_end=0.003))
        return parts
    return fn


# --------------------------------------------------------------------------- #
# Barrel fitting: brass valve, garden hose into the rain barrel on the N tile
# --------------------------------------------------------------------------- #

def build_barrel_connector(k: Kit, mode_fill):
    """Fill: the hose hooks over the barrel rim and pours in. Pump: the hose screws onto
    the spigot at the foot of the barrel and draws from it."""
    arm(k, S, start=0.06)
    k.cyl("valve_body", (0, 0, PIPE_Z), 0.045, 0.10, "brass", "y", 12)
    k.cyl("valve_stem", (0, 0, PIPE_Z + 0.05), 0.012, 0.03, "brass", segs=8)
    k.box("valve_lever", (0, -0.05, PIPE_Z + 0.068), (0.018, 0.12, 0.012), "red")
    k.cyl("hose_barb", (0, 0.07, PIPE_Z), 0.022, 0.05, "brass", "y", 10)
    k.cyl("hose_collar", (0, 0.10, PIPE_Z), 0.03, 0.025, "galv", "y", 10)
    if mode_fill:
        path = [(0, 0.11, PIPE_Z), (0.02, 0.26, 0.07), (0.03, 0.46, 0.30), (0.02, 0.56, 0.62),
                (0.0, 0.64, 0.70), (0.0, 0.72, 0.64)]
        k.tube("hose", path, 0.024, "hose", 10)
        k.cyl("nozzle", (0, 0.72, 0.60), 0.026, 0.06, "brass", segs=10)
    else:
        path = [(0, 0.11, PIPE_Z), (0.03, 0.30, 0.04), (0.02, 0.48, 0.06), (0.0, 0.60, 0.10)]
        k.tube("hose", path, 0.024, "hose", 10)
        k.cyl("spigot_nut", (0, 0.63, 0.10), 0.03, 0.04, "brass", "y", 10)
        k.cyl("spigot", (0, 0.68, 0.10), 0.02, 0.06, "brass", "y", 10)


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
    """Every render group. `lit` builds the overlay (base as holdout); `glow` is the light colour
    the style step pushes its pixels toward (None: water, composited as rendered)."""
    def g(key, facings, build, lit=None, glow=None):
        return {"key": key, "facings": facings, "build": build, "lit": lit, "glow": glow}

    green, amber = (70, 255, 90), (255, 170, 30)
    groups = [g(f"pipe_m{m:02d}", "1", (lambda m: lambda k: build_pipe(k, m))(m)) for m in range(16)]
    groups += [
        g("valve_open_ns", "1", lambda k: build_valve(k, False, False)),
        g("valve_closed_ns", "1", lambda k: build_valve(k, True, False)),
        g("valve_open_ew", "1", lambda k: build_valve(k, False, True)),
        g("valve_closed_ew", "1", lambda k: build_valve(k, True, True)),
        g("flowmeter_ns", "1", lambda k: build_flowmeter(k, False)),
        g("flowmeter_ew", "1", lambda k: build_flowmeter(k, True)),
        g("pump_off", "4", lambda k: build_pump(k)),
        g("pump_on", "4", lambda k: build_pump(k), lambda k: build_pump_lit(k), green),
        g("pump_filter_on", "4", lambda k: build_pump(k, True), lambda k: build_pump_lit(k, True), green),
        g("house_inlet", "4", build_house_inlet, build_house_inlet_lit("green"), green),
        g("house_inlet_unfiltered", "4", build_house_inlet, build_house_inlet_lit("amber"), amber),
        g("sprinkler_manual_off", "4", lambda k: build_sprinkler(k, False, False)),
        g("sprinkler_manual_on", "4", lambda k: build_sprinkler(k, True, False), build_sprinkler_lit(False)),
        g("sprinkler_auto_off", "4", lambda k: build_sprinkler(k, False, True)),
        g("sprinkler_auto_on", "4", lambda k: build_sprinkler(k, True, True), build_sprinkler_lit(True)),
        g("barrel_fill", "4", lambda k: build_barrel_connector(k, True)),
        g("barrel_pump", "4", lambda k: build_barrel_connector(k, False)),
    ]
    return groups


def lit_key(key: str) -> str:
    return f"{key}__lit"


def build(subject, mats) -> None:
    """Showcase of every part in a row (editable .blend, depth tools)."""
    k = Kit(subject, mats)
    for i, group in enumerate(tile_groups()[16:]):
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
        render_group(props, subject, mats, group["key"], group["facings"], group["build"], out)
        if group["lit"]:
            render_group(props, subject, mats, lit_key(group["key"]), group["facings"], group["lit"], out)
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


if __name__ == "__main__":
    if bpy is None:
        if len(sys.argv) < 3 or sys.argv[1] != "style":
            raise SystemExit("usage: python build_livewater_tiles.py style <out-dir> [<key>...]")
        style(Path(sys.argv[2]), set(sys.argv[3:]))
    else:
        main()
