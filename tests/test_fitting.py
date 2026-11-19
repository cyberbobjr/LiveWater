"""E20: barrel fitting (ADR-001 D26, P02, P17; Fill only, ADR-012 D02): part LiveWater:BarrelFitting set between a
pipe and a barrel, an outlet: the network fills the barrel, no leak; sprite by the shape of the container (data table,
extendable through the API, unknown = tall)."""
import json
import os
import sys
import unittest

from lwt_fakes import CONTAINERS, services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
FITTING = "shared/LiveWater/Parts/LWT_PartBarrelFitting.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class FittingPart(unittest.TestCase):
    def test_definition_follows_the_tile_contract(self):
        lua = new_lua(API, FITTING)
        d = lua.eval('LiveWater.API.part("LiveWater:BarrelFitting")')
        for key, base in (("fill", 64), ("fill_low", 68)):
            self.assertEqual([d.variants[key][i] for i in range(1, 5)], [TILE + str(base + k) for k in range(4)], key)
        self.assertEqual(d.capabilities.fitting.rate, 50)
        self.assertGreaterEqual(lua.eval("LiveWater.API.revision"), 11)

    def test_the_look_follows_the_shape(self):
        lua = new_lua(API, FITTING)
        lua.execute('P = { type = "LiveWater:BarrelFitting", data = {} }')
        self.assertEqual(lua.eval("LiveWater.Parts:look(P)"), "fill")
        lua.execute('LiveWater.Parts:call(P, "sense", { found = true, shape = "low", amount = 0, free = 400 })')
        self.assertEqual(lua.eval("LiveWater.Parts:look(P)"), "fill_low")


class Shapes(unittest.TestCase):
    def test_low_crate_collectors_are_low_unknown_is_tall_and_the_api_adds(self):
        lua = new_lua(API, FITTING)
        for sprite in ("carpentry_02_52", "carpentry_02_54", "carpentry_02_120", "carpentry_02_121"):
            self.assertEqual(lua.eval('LiveWater.Containers:shapeOf("%s")' % sprite), "low", sprite)
        self.assertEqual(lua.eval('LiveWater.Containers:shapeOf("carpentry_02_122")'), "tall")
        self.assertEqual(lua.eval('LiveWater.Containers:shapeOf(nil, "RainCollector")'), "tall")
        self.assertEqual(call(lua, 'LiveWater.API.registerContainer("my_tub_0", { shape = "low" })'), (True, None))
        self.assertEqual(lua.eval('LiveWater.Containers:shapeOf("my_tub_0")'), "low")
        self.assertEqual(call(lua, 'LiveWater.API.registerContainer("my_tub_1", { shape = "round" })'),
                         (False, "invalid_definition"))


BENCH = CONTAINERS + r"""
NEED = {}
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
FITTINGS = require("LiveWater/LWT_Fittings").new({ catalog = LiveWater.Parts, registry = REG, world = WORLD,
    containers = CONTAINERS, shapes = LiveWater.Containers, publisher = PUB })
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
OUTLETS:register("barrelFill", FITTINGS)
OUTLETS:register("sprinkler", { need = function(_, part) return NEED[part.x .. "," .. part.y] or 0 end,
    deliver = function() end })
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
LiveWater.Events.on("waterDrawn", function(part, litres) FITTINGS:drawn(part, litres) end)
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, publisher = PUB, chores = { FITTINGS },
    power = { powered = function() return true end }, need = function(part) return OUTLETS:need(part) end })
place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24")
place("Test:Pipe", 1, 0)
place("LiveWater:BarrelFitting", 2, 0, "batman_livewater_01_64")
FIT = REG:at(2, 0, 0)
function tick() EMITTED = {} CLOCK:tick() end
function state(x, y) return REG:at(x, y, 0).data.fitting.state end
"""


def bench():
    lua = services(new_lua, POND, FITTING)
    lua.execute(BENCH)
    return lua


class Fill(unittest.TestCase):
    def test_the_network_fills_the_barrel_behind_the_fitting(self):
        lua = bench()
        lua.execute('CONT["2,-1"] = { amount = 0, capacity = 400, sprite = "carpentry_02_122" } tick()')
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 50)
        self.assertEqual(lua.eval('CONT["2,-1"].fluid'), "tainted")
        self.assertEqual(lua.eval('state(2, 0)'), "served")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "188")   # pipe from the W: bent

    def test_a_low_crate_collector_draws_the_low_sprite(self):
        lua = bench()
        lua.execute('CONT["2,-1"] = { amount = 0, capacity = 400, sprite = "carpentry_02_54" } tick()')
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "196")

    def test_no_leak_a_full_barrel_or_none_takes_nothing(self):
        lua = bench()
        lua.execute('CONT["2,-1"] = { amount = 400, capacity = 400, fluid = "clean" } tick()')
        self.assertEqual(lua.eval('state(2, 0)'), "idle")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 400)
        lua.execute('CONT["2,-1"] = nil tick()')
        self.assertEqual(lua.eval('state(2, 0)'), "idle")
        lines = [l[1] for l in lua.eval("LiveWater.Parts:lines(FIT)").values()]
        self.assertIn("IGUI_LWT_Fitting_NoBarrel", lines)


class Texts(unittest.TestCase):
    def test_scripts_and_translations(self):
        with open(os.path.join(MEDIA, "scripts", "LWT_moveables.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"item Mov_LiveWater_BarrelFitting\s*\{[^}]*WorldObjectSprite = batman_livewater_01_64,")
        with open(os.path.join(MEDIA, "scripts", "LWT_recipes.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"(?s)craftRecipe LWTBuildBarrelFitting\s*\{.*?item 1 Base\.Mov_LiveWater_BarrelFitting,")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            ui = load("IG_UI.json")
            for key in ("IGUI_LWT_Fitting_NoBarrel",
                        "IGUI_LWT_Fitting_wrong_fluid", "IGUI_LWT_Outlet_wrong_fluid", "IGUI_LWT_Sprinkler_wrong_fluid",
                        "IGUI_LWT_Fluid_fuel", "IGUI_LWT_Fitting_Content"):
                self.assertIn(key, ui, lang)
            self.assertIn("LWTBuildBarrelFitting", load("Recipes.json"), lang)


#: Branch shapes of the fitting (ADR-008 D01, D01b): mask of the relative sides linked (1 front, 2 side +1, 8 side +3;
#: the barrel behind, 4, is not drawn) -> variant suffix, and first index of the four facings of each mode.
SHAPES = {2: "bend1", 8: "bend3", 10: "tee", 3: "front1", 9: "front3", 11: "cross"}
FIRST = {
    "fill": {"bend1": 184, "bend3": 188, "tee": 208, "front1": 212, "front3": 216, "cross": 220},
    "fill_low": {"bend1": 192, "bend3": 196, "tee": 224, "front1": 228, "front3": 232, "cross": 236},
}
STRAIGHT = {"fill": 64, "fill_low": 68}
#: Offset of the square on each facing 1..4 (S, E, N, W).
OFFSET = {1: (0, 1), 2: (1, 0), 3: (0, -1), 4: (-1, 0)}


def side_square(facing, rel):
    """Square on the relative side `rel` (0 front, 1, 2 behind, 3) of a fitting at (0, 0) with `facing`."""
    return OFFSET[(facing - 1 + rel) % 4 + 1]


def lone_fitting(facing):
    lua = services(new_lua, FITTING)
    lua.execute('place("LiveWater:BarrelFitting", 0, 0, "%s%d")' % (TILE, 63 + facing))
    return lua


class Branches(unittest.TestCase):
    def test_definition_declares_the_shapes_by_relative_mask(self):
        lua = new_lua(API, FITTING)
        d = lua.eval('LiveWater.API.part("LiveWater:BarrelFitting")')
        self.assertEqual({m: d.branches[m] for m in SHAPES}, SHAPES)
        for mode, firsts in FIRST.items():
            for shape, base in firsts.items():
                key = "%s_%s" % (mode, shape)
                self.assertEqual([d.variants[key][i] for i in range(1, 5)], [TILE + str(base + k) for k in range(4)],
                                 key)
                for facing in range(1, 5):
                    self.assertEqual(lua.eval('LiveWater.Parts:facingOf("%s%d")' % (TILE, base + facing - 1)), facing)

    def test_every_combination_of_front_and_side_pipes_on_every_facing(self):
        for facing in range(1, 5):
            for mask in (0, 1, 2, 3, 8, 9, 10, 11):
                lua = lone_fitting(facing)
                for rel in (0, 1, 3):
                    if mask & (1 << rel):
                        lua.execute('place("Test:Pipe", %d, %d)' % side_square(facing, rel))
                base = FIRST["fill"][SHAPES[mask]] if mask in SHAPES else STRAIGHT["fill"]
                self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + str(base + facing - 1), (facing, mask))

    def test_a_pipe_behind_is_not_drawn(self):
        lua = lone_fitting(1)
        lua.execute('place("Test:Pipe", 0, -1)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "64")
        lua.execute('place("Test:Pipe", -1, 0) place("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "208")

    def test_the_shape_follows_the_pipes_that_come_and_go(self):
        lua = lone_fitting(1)
        lua.execute('place("Test:Pipe", -1, 0)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "188")
        lua.execute('place("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "208")
        lua.execute('place("Test:Pipe", 0, 1)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "220")
        lua.execute("TOPO:remove(-1, 0, 0) WORLD:removePart(-1, 0, 0, 'Test:Pipe')")
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "212")
        lua.execute("TOPO:remove(1, 0, 0) WORLD:removePart(1, 0, 0, 'Test:Pipe')")
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "64")

    def test_the_part_and_the_tile_recipe_agree(self):
        sys.path.insert(0, os.path.join(ROOT, "source", "tiles"))
        try:
            import build_livewater_tiles as tiles
        finally:
            sys.path.pop(0)
        self.assertEqual(tiles.TOTAL, 256)
        groups = {g["key"]: g["indices"] for g in tiles.tile_groups()}
        for mode, firsts in FIRST.items():
            for shape, base in firsts.items():
                self.assertEqual(groups["barrel_%s_%s" % (mode, shape)], list(range(base, base + 4)))
                for facing in range(4):
                    self.assertEqual(tiles.tile_props(base + facing), tiles.tile_props(STRAIGHT[mode] + facing),
                                     base + facing)
        self.assertEqual(tiles.tile_props(255)["CustomItem"], "Base.Mov_LiveWater_BarrelFitting")

    def test_invalid_branches_are_refused(self):
        for bad in ('"x"', '{ [16] = "b" }', '{ [0] = "b" }', '{ [1] = 5 }', '{ [1] = "no space" }'):
            lua = new_lua(API)
            ok = lua.eval('{ LiveWater.API.registerPart("T:Bad", { variants = { on = { "b" } }, branches = %s,'
                          ' capabilities = { conduit = true } }) }' % bad)
            self.assertEqual((ok[1], ok[2]), (False, "invalid_branches"), bad)


class Through(unittest.TestCase):
    """D01b: the water goes through the fitting from one pipe to the next, the fitting still fills."""

    def test_water_goes_through_a_fitting_set_to_fill_to_a_sprinkler_downstream(self):
        lua = bench()
        lua.execute('place("Test:Pipe", 3, 0) place("Test:Spr", 4, 0) NEED["4,0"] = 20'
                    ' CONT["2,-1"] = { amount = 380, capacity = 400, fluid = "tainted" } tick()')
        self.assertEqual(lua.eval('state(2, 0)'), "served")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 400)
        self.assertEqual(lua.eval('REG:at(4, 0, 0).data.outlet.state'), "served")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "208")

if __name__ == "__main__":
    unittest.main()
