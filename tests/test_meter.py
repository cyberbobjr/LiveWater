"""E16: flow meter (ADR-001 D24, P12): part LiveWater:FlowMeter (conduit, two ports, capability meter), drawn along
its pipe (ew / ns), records the litres that went through it each step and the fluid; the part menu shows them."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
METER = "shared/LiveWater/Parts/LWT_PartFlowMeter.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"

BENCH = r"""
POWER = { powered = function() return true end }
NEED = {}
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, power = POWER, publisher = PUB,
    need = function(part) return NEED[part.x .. "," .. part.y] or 0 end })
place("LiveWater:PondPump", 0, 0) place("LiveWater:FlowMeter", 1, 0, "batman_livewater_01_21") place("Test:Spr", 2, 0)
METER = REG:at(1, 0, 0)
"""


def bench():
    lua = services(new_lua, POND, METER)
    lua.execute(BENCH)
    return lua


class Part(unittest.TestCase):
    def test_definition(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", METER)
        d = lua.eval('LiveWater.API.part("LiveWater:FlowMeter")')
        self.assertEqual((d.sprites[10], d.sprites[5]), (TILE + "20", TILE + "21"))
        self.assertIsNone(d.sprites[0])
        self.assertEqual(d.capabilities.conduit.ports, 2)
        self.assertIsNotNone(d.capabilities.meter)

    def test_drawn_along_its_pipe_and_two_ports_only(self):
        lua = bench()
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "20")
        lua.execute('place("Test:Pipe", 1, 1)')
        self.assertEqual(lua.eval('{ TOPO:canAdd("Test:Pipe", 1, -1, 0) }')[2], "ports_full")


class Measure(unittest.TestCase):
    def test_litres_through_and_fluid(self):
        lua = bench()
        lua.execute('NEED["2,0"] = 30 CLOCK:tick()')
        self.assertEqual(lua.eval("METER.data.meter.litres"), 30)
        self.assertEqual(lua.eval("METER.data.meter.quality"), "tainted")
        lines = lua.eval("LiveWater.Parts:lines(METER)")
        self.assertEqual(list(lines[1].values()), ["IGUI_LWT_Meter_Flow", 30])
        self.assertEqual(list(lines[2].values()), ["IGUI_LWT_Meter_Water_tainted"])
        lua.execute('NEED["2,0"] = 0 CLOCK:tick()')
        self.assertEqual(lua.eval("METER.data.meter.litres"), 0)
        self.assertEqual(lua.eval("#LiveWater.Parts:lines(METER)"), 1)

    def test_clean_after_a_filter(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(REG:at(0, 0, 0), "fit", 1) NEED["2,0"] = 10 CLOCK:tick()')
        self.assertEqual(lua.eval("METER.data.meter.quality"), "clean")

    def test_only_the_water_going_through_it_counts(self):
        lua = bench()
        lua.execute('place("Test:Spr", 0, 1) NEED["0,1"] = 20 NEED["2,0"] = 5 CLOCK:tick()')
        self.assertEqual(lua.eval("METER.data.meter.litres"), 5)


def script(name):
    with open(os.path.join(MEDIA, "scripts", name), encoding="ascii") as f:
        return f.read()


class Scripts(unittest.TestCase):
    def test_moveable_recipe_and_texts(self):
        self.assertRegex(script("LWT_moveables.txt"), r"item Mov_LiveWater_FlowMeter\s*\{[^}]*ItemType = base:moveable,"
                                                       r"[^}]*WorldObjectSprite = batman_livewater_01_20,")
        self.assertRegex(script("LWT_recipes.txt"), r"craftRecipe LWTBuildFlowMeter[\s\S]*item 1 Base\.Mov_LiveWater_FlowMeter")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            for key in ("IGUI_LWT_Meter_Flow", "IGUI_LWT_Meter_Water_clean", "IGUI_LWT_Meter_Water_tainted"):
                self.assertIn(key, load("IG_UI.json"), lang)
            self.assertIn("LWTBuildFlowMeter", load("Recipes.json"), lang)
            self.assertIn("Base.Mov_LiveWater_FlowMeter", load("ItemName.json"), lang)


if __name__ == "__main__":
    unittest.main()
