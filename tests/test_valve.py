"""E22 (P11): inline shut-off valve, part LiveWater:Valve (conduit with two ports, valve open when placed, manual
controller), set down between two pipes with the furniture cursor (moveable Base.Mov_LiveWater_Valve). Drawn along its
pipe by its state (open 16 ew / 17 ns, closed 18 ew / 19 ns); closed, it cuts the water after it (ADR-001 D02, D13)."""
import glob
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
VALVE = "shared/LiveWater/Parts/LWT_PartValve.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"

BENCH = r"""
POWER = { powered = function() return true end }
NEED = {}
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, power = POWER, publisher = PUB,
    need = function(part) return NEED[part.x .. "," .. part.y] or 0 end })
place("LiveWater:PondPump", 0, 0) place("LiveWater:Valve", 1, 0, "batman_livewater_01_17") place("Test:Spr", 2, 0)
VALVE = REG:at(1, 0, 0)
"""


def bench():
    lua = services(new_lua, POND, VALVE)
    lua.execute(BENCH)
    return lua


class Part(unittest.TestCase):
    def test_definition(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", VALVE)
        d = lua.eval('LiveWater.API.part("LiveWater:Valve")')
        # variant facings: 1 = S (the ns tile), 2 = E (the ew tile), as the tiles' Facing property
        self.assertEqual((d.variants.open[1], d.variants.open[2]), (TILE + "17", TILE + "16"))
        self.assertEqual((d.variants.closed[1], d.variants.closed[2]), (TILE + "19", TILE + "18"))
        self.assertEqual((d.facings[10], d.facings[5], d.facings[2], d.facings[4]), (2, 1, 2, 1))
        self.assertEqual(d.capabilities.conduit.ports, 2)
        self.assertTrue(d.capabilities.valve.open)
        self.assertTrue(d.capabilities.valve.look)
        self.assertEqual(d.capabilities.controller.mode, "manual")

    def test_drawn_along_its_pipe_and_two_ports_only(self):
        lua = bench()
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "16")
        # linked west (pump) and east (sprinkler): a third pipe is refused
        self.assertEqual(lua.eval('{ TOPO:canAdd("Test:Pipe", 1, 1, 0) }')[2], "ports_full")

    def test_turns_with_the_pipe_on_a_north_south_run(self):
        lua = services(new_lua, VALVE)
        lua.execute('place("Test:Pipe", 0, 0) place("LiveWater:Valve", 0, 1, "batman_livewater_01_16")')
        self.assertEqual(lua.eval("WORLD:sprite(0, 1, 0)"), TILE + "17")
        lua.execute('place("Test:Pipe", 0, 2)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 1, 0)"), TILE + "17")

    def test_closed_shows_the_closed_tile_along_its_axis(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(VALVE, "open", false) PUB:present(VALVE)')
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "18")
        lua.execute('LiveWater.Parts:call(VALVE, "open", true) PUB:present(VALVE)')
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "16")

    def test_menu_offers_close_then_open(self):
        lua = bench()
        acts = lua.eval("LiveWater.Parts:actions(VALVE)")
        self.assertEqual((acts[1].command, acts[1].key), ("switchValve", "ContextMenu_LWT_CloseValve"))
        lua.execute('LiveWater.Parts:call(VALVE, "open", false)')
        self.assertEqual(lua.eval("LiveWater.Parts:actions(VALVE)")[1].key, "ContextMenu_LWT_OpenValve")
        self.assertEqual(lua.eval("LiveWater.Parts:lines(VALVE)")[1][1], "IGUI_LWT_Valve_Closed")

    def test_network_view_greys_a_closed_valve(self):
        lua = bench()
        self.assertIsNone(lua.eval('LiveWater.Parts:first(VALVE, "status")'))
        lua.execute('LiveWater.Parts:call(VALVE, "open", false)')
        self.assertEqual(lua.eval('LiveWater.Parts:first(VALVE, "status")')[0], "closed")


class Water(unittest.TestCase):
    def test_open_lets_water_through(self):
        lua = bench()
        lua.execute('NEED["2,0"] = 10 CLOCK:tick()')
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.outlet.state"), "served")

    def test_closed_cuts_everything_after_it(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(VALVE, "open", false) NEED["2,0"] = 10 CLOCK:tick()')
        self.assertNotEqual(lua.eval("REG:at(2, 0, 0).data.outlet.state"), "served")


class Facings(unittest.TestCase):
    def test_invalid_facings_are_refused(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua")
        res = lua.eval('{ LiveWater.Parts:register("T:V", { variants = { a = { "x1", "x2" } }, facings = { [10] = 5 },'
                       ' capabilities = { conduit = true } }) }')
        self.assertEqual((res[1], res[2]), (False, "invalid_facings"))
        res = lua.eval('{ LiveWater.Parts:register("T:W", { variants = { a = { "y1" } }, facings = "x",'
                       ' capabilities = { conduit = true } }) }')
        self.assertEqual((res[1], res[2]), (False, "invalid_facings"))

    def test_a_mask_without_a_facing_keeps_the_facing_it_was_set_down_with(self):
        lua = services(new_lua, VALVE)
        lua.execute('place("LiveWater:Valve", 0, 0, "batman_livewater_01_17")')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "17")
        lua.execute('place("Test:Pipe", 1, 0) place("Test:Pipe", 0, 1)')
        # a bend (E + S): no facing for its mask, the valve keeps its last tile
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "16")


def script(name):
    with open(os.path.join(MEDIA, "scripts", name), encoding="ascii") as f:
        return f.read()


class Scripts(unittest.TestCase):
    def test_moveable_recipe_and_texts(self):
        self.assertRegex(script("LWT_moveables.txt"), r"item Mov_LiveWater_Valve\s*\{[^}]*ItemType = base:moveable,"
                                                       r"[^}]*WorldObjectSprite = batman_livewater_01_16,")
        self.assertRegex(script("LWT_recipes.txt"), r"craftRecipe LWTBuildValve[\s\S]*item 1 Base\.Mov_LiveWater_Valve")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang_dir in glob.glob(os.path.join(tr, "*")):
            with open(os.path.join(lang_dir, "Recipes.json"), encoding="utf-8") as f:
                self.assertIn("LWTBuildValve", json.load(f), os.path.basename(lang_dir))


if __name__ == "__main__":
    unittest.main()
