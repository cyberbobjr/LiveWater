"""E25: containers filled by the network (ADR-001 L08, D26, D28): a barrel fitting set to Fill works with any
registered container, whatever its size: barrels and rain collectors (20 L or more), water coolers by default, the
names (sprite or entity script) listed in a sandbox string option, and those registered through the API; a drinking
container (water cooler) takes clean water only."""
import os
import re
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
from test_fitting import BENCH, FITTING, POND

API = "shared/LiveWater/LWT_API.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Registry(unittest.TestCase):
    def test_water_coolers_are_registered_by_default_and_take_clean_water(self):
        lua = new_lua(API)
        self.assertTrue(lua.eval('LiveWater.Containers:admits(15, nil, "WaterDispenser", {})'))
        self.assertTrue(lua.eval('LiveWater.Containers:find(nil, "WaterDispenser").clean'))

    def test_barrels_by_size_listed_and_registered_names(self):
        lua = new_lua(API)
        self.assertTrue(lua.eval('LiveWater.Containers:admits(400, "carpentry_02_122", nil, {})'))
        self.assertFalse(lua.eval('LiveWater.Containers:admits(5, "my_jug_0", nil, {})'))
        self.assertTrue(lua.eval('LiveWater.Containers:admits(5, "my_jug_0", nil, { my_jug_0 = true })'))
        self.assertEqual(call(lua, 'LiveWater.API.registerContainer("Mod:Tank", { clean = true })'), (True, None))
        self.assertTrue(lua.eval('LiveWater.Containers:admits(5, nil, "Mod:Tank", {})'))
        self.assertEqual(call(lua, 'LiveWater.API.registerContainer("Mod:Bad", { clean = 3 })'),
                         (False, "invalid_definition"))

    def test_the_sandbox_list_is_parsed(self):
        lua = new_lua(API)
        t = lua.eval('require("LiveWater/LWT_Containers").parseList(" WaterDispenser; my_tiles_3 ;;Base.Thing ")')
        self.assertEqual(sorted(k for k in t.keys()), ["Base.Thing", "WaterDispenser", "my_tiles_3"])
        self.assertEqual(len(lua.eval('require("LiveWater/LWT_Containers").parseList(nil)')), 0)


class CleanOnly(unittest.TestCase):
    def test_a_cooler_refuses_unfiltered_water_and_takes_filtered_water(self):
        lua = services(new_lua, POND, FITTING)
        lua.execute(BENCH)
        lua.execute(r"""
        local at = CONTAINERS.at
        function CONTAINERS:at(x, y, z)
            local c = at(self, x, y, z)
            if c then c.entity = "WaterDispenser" end
            return c
        end
        CONT["2,-1"] = { amount = 0, capacity = 15 }
        tick()
        """)
        self.assertEqual(lua.eval("state(2, 0)"), "unfiltered")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 0)
        lua.execute('REG:at(0, 0, 0).data.filter = { fitted = true, used = 0, capacity = 500 } tick()')
        self.assertEqual(lua.eval("state(2, 0)"), "served")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 15)
        self.assertEqual(lua.eval('CONT["2,-1"].fluid'), "clean")


class Texts(unittest.TestCase):
    def test_sandbox_option(self):
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"option LiveWater\.FillContainers\s*\{\s*type = string, default = WaterDispenser,")
        import json
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            with open(os.path.join(tr, lang, "Sandbox.json"), encoding="utf-8") as f:
                self.assertIn("Sandbox_LWT_FillContainers_tooltip", json.load(f), lang)


if __name__ == "__main__":
    unittest.main()
