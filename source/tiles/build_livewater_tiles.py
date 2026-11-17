"""Provisional (placeholder) tiles of LiveWater, for the D23 presentation board.

Simple shapes only: they show what each part looks like and how it connects,
not the final art. Nothing here is packed into the mod before the user's
validation (ADR-001 D23, plan step E06).

Needs pz-sprite-forge (MIT). Render headless (never through the MCP as is: a
headless run works in the factory scene):
    set PZ_FORGE=E:\\pz-tools\\pz-sprite-forge
    blender -b --factory-startup -P source/tiles/build_livewater_tiles.py -- <out-dir>
Writes <out-dir>/cells/<sprite>_<facing>_x0_y0.png (128x256 cells),
<out-dir>/network.png (assembled example network) and <out-dir>/items/*.png.

Conventions: 1 Blender metre = 1 tile, tile centre at the origin, front (S) toward
-Y. Pipe sides are a 4-bit mask: N=1, E=2, S=4, W=8.
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

FORGE = Path(os.environ.get("PZ_FORGE", r"E:\pz-tools\pz-sprite-forge"))
sys.path.insert(0, str(FORGE / "blender"))

import pz_sprite_forge as F  # noqa: E402

PIPE_Z = 0.12   # pipe axis height above the floor
PIPE_R = 0.055  # pipe radius (readability: thicker than life)
N, E, S, W = 1, 2, 4, 8
DIRS = {N: (0, 1), E: (1, 0), S: (0, -1), W: (-1, 0)}

PAINTS = {
    "pipe": ("metal", (0.56, 0.60, 0.63)),
    "fitting": ("metal", (0.70, 0.52, 0.24)),
    "dark": ("metal", (0.17, 0.18, 0.19)),
    "red": ("metal", (0.78, 0.14, 0.10)),
    "green": ("metal", (0.20, 0.72, 0.28)),
    "amber": ("metal", (0.92, 0.62, 0.12)),
    "blue": ("metal", (0.16, 0.42, 0.80)),
    "motor": ("metal", (0.18, 0.36, 0.52)),
    "white": ("metal", (0.90, 0.90, 0.86)),
    "filter": ("metal", (0.30, 0.55, 0.66)),
    "charcoal": ("metal", (0.10, 0.10, 0.10)),
    "cloth": ("fabric", (0.80, 0.76, 0.62)),
    "wood": ("wood", (0.50, 0.36, 0.22)),
    "spray": ("metal", (0.62, 0.84, 0.98)),
    "hose": ("metal", (0.12, 0.14, 0.12)),
    "wall": ("brick", (0.76, 0.70, 0.58)),
    "roof": ("metal", (0.34, 0.24, 0.20)),
    "grass": ("fabric", (0.36, 0.50, 0.24)),
    "soil": ("fabric", (0.36, 0.26, 0.17)),
    "crop": ("fabric", (0.30, 0.62, 0.22)),
    "water": ("metal", (0.20, 0.42, 0.52)),
    "bank": ("fabric", (0.46, 0.40, 0.28)),
    "barrel": ("metal", (0.20, 0.38, 0.28)),
    "window": ("metal", (0.48, 0.62, 0.70)),
}

MATS: dict = {}


def materials() -> dict:
    if not MATS:
        for key, (cls, paint) in PAINTS.items():
            MATS[key] = F.forge_material(f"lwt_{key}", cls, paint)
    return MATS


# --------------------------------------------------------------------------- #
# Primitives (local coordinates of `parent`)
# --------------------------------------------------------------------------- #

def _finish(obj, parent, mat, name):
    obj.name = name
    obj.data.materials.append(MATS[mat])
    obj.parent = parent
    return obj


def box(parent, name, c, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=c, rotation=rot)
    obj = bpy.context.active_object
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return _finish(obj, parent, mat, name)


def cyl(parent, name, c, r, depth, axis, mat, verts=24):
    rot = {"x": (0, math.pi / 2, 0), "y": (math.pi / 2, 0, 0), "z": (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=c, rotation=rot)
    return _finish(bpy.context.active_object, parent, mat, name)


def sphere(parent, name, c, r, mat, seg=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=c)
    return _finish(bpy.context.active_object, parent, mat, name)


def tube(parent, name, points, r, mat):
    """Bezier tube through `points`, converted to a mesh (the forge renders meshes)."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = r
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, p in zip(spline.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    return _finish(obj, parent, mat, name)


def arm(parent, side, mat="pipe", start=0.0, z=PIPE_Z, r=PIPE_R, tag=""):
    """Pipe from `start` metres off the centre to the tile edge on `side`, with an edge flange."""
    dx, dy = DIRS[side]
    length = 0.5 - start
    mid = start + length / 2
    axis = "x" if dx else "y"
    cyl(parent, f"arm{side}{tag}", (dx * mid, dy * mid, z), r, length, axis, mat)
    cyl(parent, f"flange{side}{tag}", (dx * 0.47, dy * 0.47, z), r * 1.35, 0.035, axis, "fitting")


def saddle(parent, name, c, along_x):
    size = (0.10, 0.20, PIPE_Z - PIPE_R + 0.01) if along_x else (0.20, 0.10, PIPE_Z - PIPE_R + 0.01)
    box(parent, name, (c[0], c[1], size[2] / 2), size, "wood")


# --------------------------------------------------------------------------- #
# Parts (each modelled for facing S: its main connection or front toward -Y)
# --------------------------------------------------------------------------- #

def build_pipe(p, mask):
    sides = [s for s in (N, E, S, W) if mask & s]
    for s in sides:
        arm(p, s)
    straight = mask in (N | S, E | W)
    if not sides:
        cyl(p, "stub", (0, 0, PIPE_Z), PIPE_R, 0.36, "y", "pipe")
        for y in (-0.18, 0.18):
            cyl(p, f"cap{y}", (0, y, PIPE_Z), PIPE_R * 1.3, 0.04, "y", "fitting")
        saddle(p, "saddle", (0, 0), False)
        return
    if len(sides) == 1:
        dx, dy = DIRS[sides[0]]
        cyl(p, "cap", (0, 0, PIPE_Z), PIPE_R * 1.3, 0.05, "x" if dx else "y", "fitting")
    elif not straight:
        sphere(p, "joint", (0, 0, PIPE_Z), PIPE_R * 1.45, "fitting")
    saddle(p, "saddle", (0, 0), mask == E | W or sides[0] in (E, W) and len(sides) == 1)


def build_valve(p, closed, along_x):
    a, b = (E, W) if along_x else (N, S)
    arm(p, a, start=0.10)
    arm(p, b, start=0.10)
    axis = "x" if along_x else "y"
    cyl(p, "body", (0, 0, PIPE_Z), PIPE_R * 1.9, 0.22, axis, "fitting", 6)
    sphere(p, "ball", (0, 0, PIPE_Z), PIPE_R * 2.0, "fitting")
    cyl(p, "stem", (0, 0, PIPE_Z + 0.14), 0.018, 0.12, "z", "dark", 10)
    # Quarter-turn lever: along the pipe = open, across = closed.
    lever_x = along_x != closed
    size = (0.34, 0.05, 0.025) if lever_x else (0.05, 0.34, 0.025)
    off = (0.11, 0, 0) if lever_x else (0, -0.11, 0)
    box(p, "lever", (off[0], off[1], PIPE_Z + 0.20), size, "red")
    saddle(p, "saddle_a", (0.32 if along_x else 0, 0 if along_x else 0.32), along_x)
    saddle(p, "saddle_b", (-0.32 if along_x else 0, 0 if along_x else -0.32), along_x)


def build_flowmeter(p, along_x):
    a, b = (E, W) if along_x else (N, S)
    arm(p, a, start=0.12)
    arm(p, b, start=0.12)
    cyl(p, "body", (0, 0, PIPE_Z), PIPE_R * 2.2, 0.26, "x" if along_x else "y", "fitting", 8)
    cyl(p, "neck", (0, 0, PIPE_Z + 0.15), 0.035, 0.14, "z", "dark", 12)
    cyl(p, "gauge", (0, 0, PIPE_Z + 0.27), 0.12, 0.06, "z", "dark", 32)
    cyl(p, "face", (0, 0, PIPE_Z + 0.301), 0.10, 0.006, "z", "white", 32)
    box(p, "needle", (0.03, -0.02, PIPE_Z + 0.307), (0.08, 0.012, 0.006), "red", (0, 0, 0.6))
    saddle(p, "saddle", (0, 0), along_x)


def build_pump(p, on, with_filter=False):
    """Pond pump: intake hose over the S edge (water side), outlet pipe to the N edge."""
    box(p, "skid", (0, 0.02, 0.04), (0.72, 0.56, 0.08), "wood")
    cyl(p, "motor", (0.10, 0.08, 0.27), 0.17, 0.42, "x", "motor", 32)
    for i, x in enumerate((-0.06, 0.02, 0.10, 0.18, 0.26)):
        cyl(p, f"fin{i}", (x, 0.08, 0.27), 0.185, 0.018, "x", "motor", 32)
    cyl(p, "endcap", (0.33, 0.08, 0.27), 0.12, 0.05, "x", "dark", 24)
    cyl(p, "volute", (-0.19, 0.06, 0.25), 0.16, 0.12, "x", "dark", 32)
    cyl(p, "inlet", (-0.19, -0.12, 0.22), 0.06, 0.22, "y", "dark", 16)
    box(p, "switchbox", (0.22, -0.12, 0.42), (0.16, 0.06, 0.12), "dark")
    sphere(p, "lamp", (0.22, -0.155, 0.44), 0.03, "green" if on else "red")
    # Intake hose, down to a strainer in the water beyond the S edge.
    tube(p, "hose", [(-0.19, -0.22, 0.22), (-0.19, -0.40, 0.14), (-0.15, -0.56, 0.02)], 0.05, "hose")
    cyl(p, "strainer", (-0.15, -0.58, 0.02), 0.07, 0.10, "y", "fitting", 16)
    # Outlet: up from the volute, over to the N edge at pipe height.
    tube(p, "riser", [(-0.19, 0.06, 0.41), (-0.19, 0.20, 0.30), (-0.05, 0.30, PIPE_Z), (0.0, 0.38, PIPE_Z)],
         PIPE_R, "pipe")
    cyl(p, "flangeN", (0, 0.47, PIPE_Z), PIPE_R * 1.35, 0.035, "y", "fitting")
    cyl(p, "outarm", (0, 0.42, PIPE_Z), PIPE_R, 0.12, "y", "pipe")
    if with_filter:
        cyl(p, "filter_head", (-0.02, -0.24, 0.50), 0.10, 0.05, "z", "fitting", 24)
        cyl(p, "filter", (-0.02, -0.24, 0.34), 0.085, 0.28, "z", "filter", 24)
        cyl(p, "filter_band", (-0.02, -0.24, 0.34), 0.088, 0.06, "z", "charcoal", 24)
        tube(p, "filter_link", [(-0.19, 0.06, 0.41), (-0.06, -0.20, 0.52)], 0.03, "pipe")
    if on:
        for i, (x, z) in enumerate(((0.36, 0.42), (0.40, 0.36), (0.38, 0.48))):
            box(p, f"buzz{i}", (x + 0.06, 0.08, z + 0.05), (0.07, 0.012, 0.012), "white", (0, 0.5 - i * 0.5, 0))


def build_house_inlet(p, lamp="green"):
    """Wall-mounted house inlet against the N wall (y = +0.5); pipe leaves over the S edge."""
    box(p, "plate", (0, 0.46, 0.62), (0.44, 0.05, 0.62), "dark")
    box(p, "cabinet", (0, 0.40, 0.66), (0.36, 0.10, 0.42), "white")
    box(p, "door_line", (0, 0.348, 0.66), (0.30, 0.006, 0.36), "pipe")
    cyl(p, "gauge", (-0.08, 0.34, 0.76), 0.06, 0.03, "y", "dark", 24)
    cyl(p, "gauge_face", (-0.08, 0.323, 0.76), 0.048, 0.006, "y", "white", 24)
    sphere(p, "lamp", (0.10, 0.34, 0.78), 0.035, lamp)
    cyl(p, "wallpipe", (0.0, 0.40, 0.32), PIPE_R, 0.40, "z", "pipe")
    sphere(p, "elbow", (0.0, 0.40, PIPE_Z), PIPE_R * 1.4, "fitting")
    cyl(p, "toroom", (0.0, 0.47, 0.90), 0.035, 0.10, "y", "pipe")
    arm(p, S, start=0.0)
    cyl(p, "run", (0, 0.20, PIPE_Z), PIPE_R, 0.40, "y", "pipe")


def build_sprinkler(p, active, automatic):
    """Sprinkler on a riser, fed over the S edge."""
    arm(p, S, start=0.0)
    sphere(p, "foot", (0, 0, PIPE_Z), PIPE_R * 1.5, "fitting")
    box(p, "stake", (0, 0, 0.05), (0.18, 0.18, 0.10), "wood")
    cyl(p, "riser", (0, 0, 0.30), 0.03, 0.36, "z", "pipe", 12)
    cyl(p, "head", (0, 0, 0.50), 0.06, 0.07, "z", "fitting", 16)
    box(p, "rotor", (0, 0, 0.55), (0.30, 0.03, 0.02), "fitting", (0, 0, 0.5))
    box(p, "tap", (0.05, 0, 0.20), (0.06, 0.05, 0.04), "fitting")
    box(p, "tap_lever", (0.09, 0, 0.24), (0.025, 0.12, 0.02), "red" if not active else "green")
    if automatic:
        box(p, "timer", (-0.11, -0.02, 0.30), (0.10, 0.12, 0.16), "white")
        box(p, "screen", (-0.11, -0.085, 0.33), (0.07, 0.006, 0.05), "dark")
        sphere(p, "led", (-0.11, -0.085, 0.27), 0.015, "green" if active else "amber")
        tube(p, "cable", [(-0.16, 0.0, 0.24), (-0.25, 0.10, 0.08), (-0.30, 0.30, 0.02)], 0.012, "dark")
    if active:
        for k in range(8):
            ang = k * math.pi / 4 + 0.3
            for t in (0.2, 0.4, 0.6, 0.8, 1.0):
                rr = 0.42 * t
                z = 0.56 + 0.28 * t - 0.42 * t * t
                sphere(p, f"drop{k}_{t}", (rr * math.cos(ang), rr * math.sin(ang), z),
                       0.022 - 0.008 * t, "spray", 8)


def build_barrel_connector(p, mode_fill):
    """Barrel connector: network pipe over the S edge, hose into a barrel on the N tile."""
    arm(p, S, start=0.0)
    box(p, "body", (0, 0, PIPE_Z + 0.02), (0.18, 0.18, 0.16), "fitting")
    cyl(p, "knob", (0, 0, PIPE_Z + 0.13), 0.06, 0.04, "z", "blue" if mode_fill else "amber", 20)
    box(p, "knob_mark", (0, -0.03, PIPE_Z + 0.155), (0.02, 0.06, 0.01), "white")
    tube(p, "hose", [(0, 0.08, PIPE_Z + 0.02), (0, 0.24, 0.10), (0, 0.40, 0.48), (0, 0.52, 0.62)], 0.035, "hose")
    cyl(p, "nozzle", (0, 0.50, 0.62), 0.045, 0.06, "y", "fitting", 16)
    arrow_mat = "blue" if mode_fill else "amber"
    # Direction arrow painted on the body: toward the barrel (fill) or from it (pump).
    sign = 1 if mode_fill else -1
    box(p, "arrow_shaft", (0.095, 0, PIPE_Z + 0.03), (0.006, 0.10, 0.02), arrow_mat)
    box(p, "arrow_tip", (0.095, sign * 0.06, PIPE_Z + 0.03), (0.006, 0.05, 0.05), arrow_mat, (math.pi / 4, 0, 0))


# --------------------------------------------------------------------------- #
# Inventory items
# --------------------------------------------------------------------------- #

def build_item_pipe(p):
    cyl(p, "pipe", (0, 0, 0.05), 0.05, 0.9, "x", "pipe")
    for x in (-0.44, 0.44):
        cyl(p, f"thread{x}", (x, 0, 0.05), 0.058, 0.06, "x", "fitting")


def build_item_filter(p):
    cyl(p, "shell", (0, 0, 0.25), 0.16, 0.42, "z", "filter", 32)
    cyl(p, "charcoal", (0, 0, 0.25), 0.165, 0.14, "z", "charcoal", 32)
    cyl(p, "cloth_top", (0, 0, 0.465), 0.17, 0.02, "z", "cloth", 32)
    cyl(p, "cloth_bot", (0, 0, 0.035), 0.17, 0.02, "z", "cloth", 32)
    cyl(p, "port", (0, 0, 0.50), 0.05, 0.06, "z", "fitting", 16)


# --------------------------------------------------------------------------- #
# Groups rendered as cells: (sprite base name, facings, builder)
# --------------------------------------------------------------------------- #

def tile_groups():
    groups = [(f"pipe_m{m:02d}", "1", (lambda m: lambda p: build_pipe(p, m))(m)) for m in range(16)]
    groups += [
        ("valve_open_ns", "1", lambda p: build_valve(p, False, False)),
        ("valve_closed_ns", "1", lambda p: build_valve(p, True, False)),
        ("valve_open_ew", "1", lambda p: build_valve(p, False, True)),
        ("valve_closed_ew", "1", lambda p: build_valve(p, True, True)),
        ("flowmeter_ns", "1", lambda p: build_flowmeter(p, False)),
        ("flowmeter_ew", "1", lambda p: build_flowmeter(p, True)),
        ("pump_off", "4", lambda p: build_pump(p, False)),
        ("pump_on", "4", lambda p: build_pump(p, True)),
        ("pump_filter_on", "4", lambda p: build_pump(p, True, True)),
        ("house_inlet", "4", lambda p: build_house_inlet(p)),
        ("house_inlet_unfiltered", "4", lambda p: build_house_inlet(p, "amber")),
        ("sprinkler_manual_off", "4", lambda p: build_sprinkler(p, False, False)),
        ("sprinkler_manual_on", "4", lambda p: build_sprinkler(p, True, False)),
        ("sprinkler_auto_off", "4", lambda p: build_sprinkler(p, False, True)),
        ("sprinkler_auto_on", "4", lambda p: build_sprinkler(p, True, True)),
        ("barrel_fill", "4", lambda p: build_barrel_connector(p, True)),
        ("barrel_pump", "4", lambda p: build_barrel_connector(p, False)),
    ]
    return groups


def build(subject, mats) -> None:
    """Showcase for the .blend copy: one of each part in a row."""
    for i, (_, _, fn) in enumerate(tile_groups()[16:]):
        e = bpy.data.objects.new(f"show{i}", None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = subject
        e.location = (i * 1.2, 0, 0)
        fn(e)


# --------------------------------------------------------------------------- #
# Assembled example network
# --------------------------------------------------------------------------- #

ROT = {"S": 0.0, "E": math.pi / 2, "N": math.pi, "W": -math.pi / 2}


def place(root, name, x, y, facing, fn):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.parent = root
    e.location = (x, y, 0)
    e.rotation_euler = (0, 0, ROT[facing])
    fn(e)
    return e


def build_network(root):
    # Ground, pond, garden plots, house.
    box(root, "grass", (4.0, 2.0, -0.03), (30, 30, 0.06), "grass")
    box(root, "bank", (-0.5, 4.0, -0.02), (3.6, 5.6, 0.04), "bank")
    box(root, "pond", (-0.6, 4.0, 0.0), (3.2, 5.2, 0.04), "water")
    for y in (-1, -2):
        box(root, f"plot{y}", (4.5, y, 0.0), (6.0, 0.9, 0.05), "soil")
        for x in range(2, 8):
            for dx in (-0.2, 0.2):
                sphere(root, f"crop{x}{y}{dx}", (x + dx, y, 0.12), 0.12, "crop", 10)
    box(root, "house", (7.0, 7.5, 1.2), (4.0, 4.0, 2.4), "wall")
    box(root, "roof", (7.0, 7.5, 2.5), (4.3, 4.3, 0.2), "roof")
    box(root, "window", (8.0, 5.49, 1.4), (0.9, 0.04, 0.7), "window")
    box(root, "door", (5.0, 5.49, 0.9), (0.8, 0.04, 1.8), "dark")
    box(root, "barrel", (3.0, 6.0, 0.45), (0.01, 0.01, 0.01), "barrel")
    cyl(root, "barrel_body", (3.0, 6.0, 0.45), 0.32, 0.9, "z", "barrel", 32)
    # Network: pump (water on its W side) -> cross -> house / garden / barrel.
    place(root, "pump", 1, 4, "W", lambda p: build_pump(p, True, True))
    place(root, "p_2_4", 2, 4, "S", lambda p: build_pipe(p, E | W))
    place(root, "cross", 3, 4, "S", lambda p: build_pipe(p, N | E | S | W))
    place(root, "barrelc", 3, 5, "S", lambda p: build_barrel_connector(p, True))
    place(root, "valve_h", 4, 4, "S", lambda p: build_valve(p, False, True))
    place(root, "meter", 5, 4, "S", lambda p: build_flowmeter(p, True))
    place(root, "c_6_4", 6, 4, "S", lambda p: build_pipe(p, W | N))
    place(root, "inlet", 6, 5, "S", lambda p: build_house_inlet(p))
    place(root, "valve_g", 3, 3, "S", lambda p: build_valve(p, False, False))
    place(root, "p_3_2", 3, 2, "S", lambda p: build_pipe(p, N | S))
    place(root, "t_3_1", 3, 1, "S", lambda p: build_pipe(p, N | E | S))
    place(root, "spr_m", 3, 0, "N", lambda p: build_sprinkler(p, True, False))
    place(root, "p_4_1", 4, 1, "S", lambda p: build_pipe(p, E | W))
    place(root, "p_5_1", 5, 1, "S", lambda p: build_pipe(p, E | W))
    place(root, "c_6_1", 6, 1, "S", lambda p: build_pipe(p, W | S))
    place(root, "spr_a", 6, 0, "N", lambda p: build_sprinkler(p, True, True))


def render_network(scene, out):
    root = bpy.data.objects.new("LWT_Network", None)
    scene.collection.objects.link(root)
    build_network(root)
    cam = bpy.data.objects.new("LWT_NetCam", bpy.data.cameras.new("LWT_NetCam"))
    scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 12.5
    cam.data.clip_end = 200
    target = Vector((3.6, 2.6, 0.6))
    cam.location = target + F.camera_direction() * 40
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    for name in ("PZ_Ground", "PZ_TileGuide"):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 1800, 1100
    scene.render.film_transparent = True
    scene.view_settings.exposure = 0.5
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    scene.view_settings.exposure = 0.0
    return root, cam


def render_items(scene, subject, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cam = bpy.data.objects.new("LWT_ItemCam", bpy.data.cameras.new("LWT_ItemCam"))
    scene.collection.objects.link(cam)
    cam.data.type = "PERSP"
    cam.data.lens = 60
    scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = 256
    scene.render.film_transparent = True
    for name, fn, target, dist in (("pipe_section", build_item_pipe, (0, 0, 0.05), 2.2),
                                   ("water_filter", build_item_filter, (0, 0, 0.25), 1.6)):
        clear(subject)
        fn(subject)
        t = Vector(target)
        cam.location = t + Vector((0.9, -1.4, 0.9)).normalized() * dist
        cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(Path(out_dir) / f"{name}.png")
        bpy.ops.render.render(write_still=True)


def clear(subject):
    for obj in list(subject.children_recursive):
        bpy.data.objects.remove(obj, do_unlink=True)


def main() -> None:
    out = Path(sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "build/livewater_tiles")
    if not bpy.app.background:
        scene = bpy.data.scenes.new("LWT_Tiles")
        bpy.context.window.scene = scene
    else:
        scene = bpy.context.scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    F.register()
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.footprint_x = props.footprint_y = 1
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True
    F.build_rig(bpy.context)
    scene.cycles.samples = 64
    materials()
    subject = bpy.data.objects[F.SUBJECT_NAME]
    only = os.environ.get("LWT_ONLY")
    for name, facings, fn in tile_groups():
        if only and only not in name:
            continue
        clear(subject)
        fn(subject)
        props.sheet_name = name
        props.facings = facings
        props.output_dir = str(out / "cells")
        F.render_cells(bpy.context)
        print(f"rendered {name}")
    clear(subject)
    if not only:
        render_items(scene, subject, out / "items")
        clear(subject)
        render_network(scene, str(out / "network.png"))
    print("done")


if __name__ == "__main__":
    main()
