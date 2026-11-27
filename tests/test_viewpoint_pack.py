"""ADR-019: the Viewpoint resource pack of the sub-mod batman_LiveWaterViewpoint, checked against the rules that
Viewpoint 0.1.7 applies when it discovers a pack (viewpoint.addons.Descriptor, DescriptorCheck, Ids) and loads its
models (viewpoint.packs.PackManifest, ObjReader, PackLoads). The pack is produced by
source/tiles/build_viewpoint_models.py (headless Blender); this test only reads the files."""
import math
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUB_MOD = os.path.join(ROOT, "Contents", "mods", "batman_LiveWaterViewpoint")
PACK_ID = "batman-livewater"
PACK = os.path.join(SUB_MOD, "common", "media", "viewpoint", "resourcepacks", PACK_ID)
SHEET = "batman_livewater_01"

#: ADR-019 D04: every drawn tile of the sheet; not the invisible relay (76) nor the animated jet (128-159).
BOUND = (set(range(0, 22)) | set(range(24, 76)) | set(range(104, 124)) | set(range(160, 256)))
#: Tiles drawn in four facings (S, E, N, W at index % 4); the others have one shape per sprite.
FOUR_FACINGS = set(range(24, 76)) | set(range(176, 256))
#: How far a model may reach beyond its square (pump suction hose into the water, barrel hose over the rim).
REACH = 0.75
FLOOR_HEIGHT = 2.4494896


def properties(path):
    """key=value lines, '#' comments, as java.util.Properties reads these plain files."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def obj(path):
    verts, faces, mtllib = [], [], None
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "v":
                verts.append(tuple(float(x) for x in t[1:4]))
            elif t[0] == "f":
                faces.append([int(c.split("/")[0]) - 1 for c in t[1:]])
            elif t[0] == "mtllib":
                mtllib = line.strip()[7:].strip()
    return verts, faces, mtllib


def signed_volume(verts, faces):
    vol = 0.0
    for face in faces:
        a = verts[face[0]]
        for k in range(1, len(face) - 1):
            b, c = verts[face[k]], verts[face[k + 1]]
            vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                    + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    return vol


class SubMod(unittest.TestCase):
    def test_the_sub_mod_requires_livewater(self):
        info = properties(os.path.join(SUB_MOD, "42.21", "mod.info"))
        self.assertEqual(info["id"], "batman_LiveWaterViewpoint")
        self.assertEqual(info["require"], "\\batman_LiveWater")


class LuaRegistration(unittest.TestCase):
    def test_registers_the_manifest_of_the_pack_with_literal_arguments(self):
        """ADR-019, update of 2026-11-27. Viewpoint only discovers pack.properties in the mods enabled when the
        game starts and leaves the pack off; the Lua call loads the models whenever the sub-mod is enabled.
        Viewpoint reads the call with a pattern (viewpoint.addons.LegacyPacks): both arguments are literals."""
        path = os.path.join(SUB_MOD, "common", "media", "lua", "client", "LiveWaterViewpoint.lua")
        with open(path, encoding="ascii") as f:
            calls = re.findall(r"ModelPacks\s*[.:]\s*register\s*\(([^,()]*),([^()]*)\)", f.read())
        self.assertEqual(len(calls), 1)
        mod, manifest = (a.strip() for a in calls[0])
        self.assertEqual(mod, '"batman_LiveWaterViewpoint"')
        self.assertRegex(manifest, r'^"[^"]+"$')
        descriptor = properties(os.path.join(PACK, "pack.properties"))
        self.assertEqual(os.path.normpath(os.path.join(SUB_MOD, "common", *manifest.strip('"').split("/"))),
                         os.path.normpath(os.path.join(PACK, *descriptor["models"].split("/"))))


class Descriptor(unittest.TestCase):
    def setUp(self):
        self.d = properties(os.path.join(PACK, "pack.properties"))

    def test_required_keys_and_their_formats(self):
        for key in ("format", "id", "name", "version", "game.min"):
            self.assertIn(key, self.d)
        self.assertEqual(self.d["format"], "1")
        self.assertRegex(self.d["version"], r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$")
        self.assertRegex(self.d["game.min"], r"^[0-9]+\.[0-9]+$")
        self.assertLessEqual(len(self.d.get("description", "")), 128)
        self.assertEqual(self.d["viewpoint.min"], "0.1.7")

    def test_the_id_is_a_viewpoint_id_and_the_folder_name(self):
        pid = self.d["id"]
        self.assertEqual(pid, PACK_ID)
        self.assertRegex(pid, r"^[a-z0-9]([a-z0-9-]|\.(?!\.)){0,62}[a-z0-9]$")
        self.assertFalse(pid.startswith("legacy"))

    def test_files_named_by_the_descriptor_are_inside_the_pack(self):
        for key in ("models", "icon"):
            path = self.d[key]
            self.assertNotIn("..", path.split("/"))
            self.assertFalse(path.startswith("/") or "\\" in path or ":" in path)
            self.assertTrue(os.path.isfile(os.path.join(PACK, *path.split("/"))), path)
        self.assertTrue(self.d["icon"].endswith(".png"))


class Manifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = properties(os.path.join(PACK, "pack.properties"))
        cls.manifest = os.path.join(PACK, *d["models"].split("/"))
        m = properties(cls.manifest)
        cls.models = {k[6:]: v for k, v in m.items() if k.startswith("model.")}
        cls.binds = {k[5:]: v.split(",") for k, v in m.items() if k.startswith("bind.")}

    def test_exactly_the_drawn_tiles_are_bound(self):
        self.assertEqual(set(self.binds), {f"{SHEET}_{i}" for i in BOUND})

    def test_every_bind_names_an_existing_model_turned_for_its_facing(self):
        """One model per tile group (its S facing). Viewpoint turns (X, Y) to (X cos a - Y sin a, X sin a + Y cos a)
        (viewpoint.packs.PackBind with its axes x = -X, z = -Y): E, N, W are -90, -180, -270 degrees."""
        for sprite, fields in self.binds.items():
            index = int(sprite.rsplit("_", 1)[1])
            self.assertEqual(len(fields), 6, sprite)
            self.assertIn(fields[0], self.models, sprite)
            facing = index % 4 if index in FOUR_FACINGS else 0
            self.assertEqual([float(x) for x in fields[1:]], [(-90 * facing) % 360, 0, 0, 0, 1], sprite)
            if index in FOUR_FACINGS:
                self.assertEqual(fields[0], self.binds[f"{SHEET}_{index - facing}"][0], sprite)

    def model_path(self, sprite):
        rel = self.models[self.binds[f"{SHEET}_{sprite}"][0]]
        return os.path.join(os.path.dirname(self.manifest), *rel.split("/"))

    def test_every_model_loads_like_viewpoint_reads_it(self):
        here = os.path.dirname(self.manifest)
        for name, rel in self.models.items():
            path = os.path.join(here, *rel.split("/"))
            verts, faces, mtllib = obj(path)
            self.assertTrue(faces, name)
            self.assertIsNotNone(mtllib, name)
            self.assertNotIn("..", mtllib.split("/"), name)
            mtl = os.path.join(os.path.dirname(path), *mtllib.split("/"))
            with open(mtl, encoding="utf-8") as f:
                maps = [l.split(None, 1)[1].strip() for l in f if l.startswith("map_Kd ")]
            self.assertTrue(maps, mtl)
            for tex in maps:
                with open(os.path.join(os.path.dirname(mtl), tex), "rb") as f:
                    self.assertEqual(f.read(8), b"\x89PNG\r\n\x1a\n")

    def test_faces_wind_outward_and_models_stay_on_their_square(self):
        for name, rel in self.models.items():
            verts, faces, _ = obj(os.path.join(os.path.dirname(self.manifest), *rel.split("/")))
            self.assertGreater(signed_volume(verts, faces), 0, name)
            xs, ys, zs = zip(*verts)
            self.assertLessEqual(max(map(abs, xs + ys)), REACH, name)
            self.assertGreaterEqual(min(zs), -0.1, name)
            self.assertLessEqual(max(zs), FLOOR_HEIGHT, name)

    def test_facings_follow_the_sprites_x_east_y_south(self):
        """House inlet (40-43, S E N W): its backboard stands against the wall behind it (N, W, S, E)."""
        def extent(sprite):
            verts, _, _ = obj(self.model_path(sprite))
            a = math.radians(float(self.binds[f"{SHEET}_{sprite}"][1]))
            turned = [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y, _ in verts]
            xs, ys = zip(*turned)
            return min(xs), max(xs), min(ys), max(ys)
        self.assertLess(extent(40)[2], -0.45)   # S facing: back on the N wall, y toward north
        self.assertLess(extent(41)[0], -0.45)   # E facing: back on the W wall
        self.assertGreater(extent(42)[3], 0.45)  # N facing: back on the S wall
        self.assertGreater(extent(43)[1], 0.45)  # W facing: back on the E wall

    def test_lit_lamps_glow(self):
        mtls = set()
        for rel in self.models.values():
            path = os.path.join(os.path.dirname(self.manifest), *rel.split("/"))
            _, _, mtllib = obj(path)
            mtls.add(os.path.normpath(os.path.join(os.path.dirname(path), *mtllib.split("/"))))
        glowing = set()
        for mtl in mtls:
            name = None
            with open(mtl, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("newmtl "):
                        name = line.split()[1]
                    elif line.startswith("Ke ") and any(float(x) > 0 for x in line.split()[1:4]):
                        glowing.add(name)
        self.assertEqual(glowing, {"lit_green", "lit_amber"})
        for sprite, lamp in ((28, "lit_green"), (40, "lit_green"), (44, "lit_amber"), (60, "lit_green")):
            with open(self.model_path(sprite), encoding="utf-8") as f:
                self.assertIn(f"usemtl {lamp}", f.read(), sprite)
        with open(self.model_path(24), encoding="utf-8") as f:
            self.assertFalse(re.search(r"usemtl lit_", f.read()))


if __name__ == "__main__":
    unittest.main()
