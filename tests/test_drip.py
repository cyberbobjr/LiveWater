"""ADR-004 (plan 004, G02-G04): the drip line LiveWater:DripLine. A drip outlet waters with any water, clean or not,
and refuses every other fluid (ADR-005 D03, replaces ADR-004 D05), all the
drip outlets of a network pay their pressure cost once per step (D04), a barrel fitting set to Pump on a network
without any pump gives a gravity pressure only drip outlets use (D04); each drip square waters its unlinked
neighbours N, E, S, W with 0.2 L doses and loses nothing (D02, D03); each square served draws its flow, thirsty plants
or not (ADR-006 D01, D02: sandbox DripFlow, 0.5 L); no sound (D06); part, moveable, recipe, translations (D01, D07) and
its 16 tiles (indices 160-175)."""
import json
import os
import sys
import unittest

from lwt_fakes import CONTAINERS, services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
DRIP = "shared/LiveWater/Parts/LWT_PartDripLine.lua"
FITTING = "shared/LiveWater/Parts/LWT_PartBarrelFitting.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"
LANGS = ("EN", "FR", "DE", "ES", "PT", "PTBR", "RU", "TR", "CN", "JP", "KO")

SETUP = r"""
local function part(id, caps) LiveWater.API.registerPart(id, { sprites = { [0] = "t_" .. id }, capabilities = caps }) end
part("Test:Pipe", { conduit = true })
part("Test:Pump", { intake = true, pump = true })
part("Test:CleanPump", { intake = { quality = "clean" }, pump = true })
part("Test:InlineFilter", { conduit = true, filter = true })
part("Test:Inlet", { outlet = { type = "houseInlet" } })
part("Test:Spr", { outlet = { type = "sprinkler" } })
part("Test:Drip", { conduit = true, outlet = { type = "drip" } })
part("Test:Fit", { fitting = true })
NET = require("LiveWater/LWT_Network").new(LiveWater.Parts)
FLOW = require("LiveWater/LWT_Flow").new(LiveWater.Parts)
NEED = {}
CTX = { need = function(p) return NEED[p.x .. "," .. p.y] end }
function put(t, x, y, need, data) NET:add({ type = t, x = x, y = y, z = 0, data = data }) NEED[x .. "," .. y] = need end
function barrel(x, y, fluid, amount)
    put("Test:Fit", x, y, nil, { fitting = { mode = "pump", found = true, fluid = fluid, amount = amount } })
end
function step() R = FLOW:step(NET, NET:networkAt(0, 0, 0), CTX) return R end
function state(x, y) return R.at[x .. "," .. y .. ",0"].state end
function litres(x, y) return R.at[x .. "," .. y .. ",0"].litres end
"""


def flow(layout):
    lua = new_lua(API)
    lua.execute(SETUP)
    lua.execute(layout)
    lua.execute("step()")
    return lua


class SharedCost(unittest.TestCase):
    def test_the_drip_outlets_of_a_network_pay_one_pressure_together(self):
        lua = flow("""
        put("Test:CleanPump", 0, 0)
        for x = 1, 4 do put("Test:Drip", x, 0, 1) put("Test:Spr", x, 1, 1) end
        put("Test:Spr", 5, 0, 1)
        """)
        states = [lua.eval("state(%d, 0)" % x) for x in range(1, 5)] + [lua.eval("state(%d, 1)" % x) for x in range(1, 5)]
        self.assertEqual(states, ["served"] * 8)
        self.assertEqual(lua.eval("state(5, 0)"), "served")

    def test_one_more_sprinkler_than_the_budget_still_runs_dry(self):
        lua = flow("""
        put("Test:CleanPump", 0, 0)
        for x = 1, 4 do put("Test:Drip", x, 0, 1) put("Test:Spr", x, 1, 1) end
        put("Test:Spr", 5, 0, 1) put("Test:Spr", 1, -1, 1)
        """)
        served = [lua.eval("R.outlets[%d].state" % i) for i in range(1, 11)]
        self.assertEqual(served.count("served"), 9)
        self.assertEqual(lua.eval("state(5, 0)"), "no_pressure")


# A tank that gives the pumps another fluid than water or fuel (a third-party part).
OTHER_TANK = r"""
LiveWater.API.registerCapability("juiceTank", { define = function() return {} end,
    draw = function() return 100, "juice" end })
LiveWater.API.registerPart("Test:JuiceTank", { sprites = { [0] = "t_juice" }, capabilities = { juiceTank = true } })
"""


class Quality(unittest.TestCase):
    """ADR-005 D03: irrigation (sprinkler, drip line) takes clean and tainted water, nothing else."""

    def test_sprinklers_and_drip_lines_water_with_clean_or_tainted_water(self):
        for pump in ("Test:Pump", "Test:CleanPump"):
            lua = flow('put("%s", 0, 0) put("Test:Drip", 1, 0, 1) put("Test:Spr", 0, 1, 1)' % pump)
            self.assertEqual((lua.eval("state(1, 0)"), lua.eval("state(0, 1)")), ("served", "served"), pump)

    def test_sprinklers_and_drip_lines_take_no_fuel(self):
        lua = flow('put("Test:CleanPump", 0, 0) barrel(0, -1, "fuel", 100) put("Test:Drip", 1, 0, 1)'
                   ' put("Test:Spr", 0, 1, 1)')
        self.assertEqual((lua.eval("state(1, 0)"), lua.eval("state(0, 1)")), ("wrong_fluid", "wrong_fluid"))

    def test_sprinklers_and_drip_lines_take_no_other_fluid(self):
        lua = new_lua(API)
        lua.execute(OTHER_TANK)
        lua.execute(SETUP)
        lua.execute('put("Test:CleanPump", 0, 0) put("Test:JuiceTank", 0, -1) put("Test:Drip", 1, 0, 1)'
                    ' put("Test:Spr", 0, 1, 1) put("Test:InlineFilter", -1, 0) put("Test:Inlet", -2, 0, 1) step()')
        self.assertEqual(lua.eval("R.quality"), "juice")
        self.assertEqual((lua.eval("state(1, 0)"), lua.eval("state(0, 1)")), ("wrong_fluid", "wrong_fluid"))
        self.assertEqual(lua.eval("state(-2, 0)"), "wrong_fluid")

    def test_a_filter_never_turns_another_fluid_into_clean_water(self):
        lua = new_lua(API)
        lua.execute(OTHER_TANK)
        lua.execute(SETUP)
        lua.execute('put("Test:CleanPump", 0, 0) put("Test:JuiceTank", 0, -1) put("Test:InlineFilter", 1, 0)'
                    ' put("Test:Fit", 2, 0, 5, { fitting = { mode = "fill", found = true, free = 100 } }) step()')
        self.assertEqual((lua.eval("state(2, 0)"), lua.eval('R.at["2,0,0"].quality')), ("served", "juice"))


class Gravity(unittest.TestCase):
    def test_a_barrel_without_pump_feeds_only_the_drip_lines(self):
        lua = flow("""
        barrel(0, 0, "clean", 30)
        put("Test:Drip", 1, 0, 2) put("Test:Spr", 1, 1, 1) put("Test:Drip", 2, 0, 3) put("Test:Inlet", 3, 0, 5)
        """)
        self.assertEqual(lua.eval("R.pressure"), 1)
        self.assertEqual((lua.eval("state(1, 0)"), lua.eval("state(2, 0)")), ("served", "served"))
        self.assertEqual((lua.eval("litres(1, 0)"), lua.eval("litres(2, 0)")), (2, 3))
        self.assertEqual((lua.eval("state(1, 1)"), lua.eval("state(3, 0)")), ("no_pressure", "no_pressure"))
        self.assertEqual(lua.eval('R.drawn["0,0,0"].litres'), 5)

    def test_a_barrel_set_to_fill_gives_no_gravity(self):
        lua = flow('put("Test:Fit", 0, 0) put("Test:Drip", 1, 0, 2)')
        self.assertEqual(lua.eval("#R.outlets"), 0)

    def test_tainted_barrel_water_feeds_the_drip_lines_without_filter(self):
        lua = flow('barrel(0, 0, "tainted", 30) put("Test:Drip", 1, 0, 2)')
        self.assertEqual(lua.eval("state(1, 0)"), "served")


class Area(unittest.TestCase):
    def test_the_unlinked_neighbours_are_watered_never_the_line_itself(self):
        lua = new_lua(API)
        area = lua.eval("require('LiveWater/LWT_DripArea').squares(5, 5, 10)")
        self.assertEqual(sorted((s.x, s.y) for s in area.values()), [(5, 4), (5, 6)])
        area = lua.eval("require('LiveWater/LWT_DripArea').squares(5, 5, 0)")
        self.assertEqual(sorted((s.x, s.y) for s in area.values()), [(4, 5), (5, 4), (5, 6), (6, 5)])


class DripPart(unittest.TestCase):
    def test_sixteen_shapes_a_drip_outlet_and_no_sound(self):
        lua = new_lua(API, DRIP)
        d = lua.eval('LiveWater.API.part("LiveWater:DripLine")')
        self.assertEqual([d.sprites[m] for m in range(16)], [TILE + str(160 + m) for m in range(16)])
        self.assertEqual(d.capabilities.outlet.type, "drip")
        self.assertEqual(d.capabilities.drip.dose, 0.2)
        drip = lua.eval('{ LiveWater.Parts:first({ type = "LiveWater:DripLine", data = {} }, "drip") }')
        self.assertEqual((drip[1], drip[2]), (0.2, 0.5))
        drip = lua.eval('{ LiveWater.Parts:first({ type = "LiveWater:DripLine", data = {} }, "drip",'
                        ' { scale = function(n) return n == "DripFlow" and 2 or nil end }) }')
        self.assertEqual(drip[2], 2)
        self.assertTrue(lua.eval('LiveWater.Parts:hasHook("LiveWater:DripLine", "carries")'))
        self.assertFalse(lua.eval('LiveWater.Parts:hasHook("LiveWater:DripLine", "sound")'))
        self.assertIsNone(lua.eval('LiveWater.Parts:crossing("LiveWater:DripLine", 9, 1)'))

    def test_state_lines_of_its_own(self):
        lua = new_lua(API, DRIP)
        lines = lua.eval('LiveWater.Parts:lines({ type = "LiveWater:DripLine", data = { outlet = { state = "wrong_fluid" } } })')
        self.assertIn("IGUI_LWT_Drip_wrong_fluid", [l[1] for l in lines.values()])


BENCH = CONTAINERS + r"""
FARM = { plants = {}, watered = {} }
function FARM:plant(x, y, z) return self.plants[x .. "," .. y] end
function FARM:water(x, y, z, doses)
    local p = self.plants[x .. "," .. y]
    p.level = p.level + 10 * doses
    self.watered[x .. "," .. y] = (self.watered[x .. "," .. y] or 0) + doses
    return true
end
function plant(x, y, level, needed) FARM.plants[x .. "," .. y] = { alive = true, level = level, needed = needed } end
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
FITTINGS = require("LiveWater/LWT_Fittings").new({ catalog = LiveWater.Parts, registry = REG, world = WORLD,
    containers = CONTAINERS, shapes = LiveWater.Containers, publisher = PUB })
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
SCALE = {}
OUTLETS:register("drip", require("LiveWater/LWT_Plants").new({ farming = FARM,
    area = require("LiveWater/LWT_DripArea").reach(LiveWater.Parts, NET, function(n) return SCALE[n] end) }))
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
LiveWater.Events.on("waterDrawn", function(part, litres) FITTINGS:drawn(part, litres) end)
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, publisher = PUB, chores = { FITTINGS },
    need = function(part) return OUTLETS:need(part) end })
place("LiveWater:BarrelFitting", 0, 0, "batman_livewater_01_72")
LiveWater.Parts:call(REG:at(0, 0, 0), "setFittingMode", "pump")
for x = 1, 3 do place("LiveWater:DripLine", x, 0) end
function tick() EMITTED = {} CLOCK:tick() end
"""


class Watering(unittest.TestCase):
    def bench(self, fluid, setup=""):
        lua = services(new_lua, FITTING, DRIP)
        lua.execute(BENCH)
        lua.execute('CONT["0,-1"] = { amount = 30, capacity = 400, fluid = "%s" }' % fluid)
        lua.execute(setup + " plant(2, 1, 0, 20) plant(4, 0, 0, 10) plant(2, 0, 0, 10) plant(0, 1, 0, 10) tick()")
        return lua

    def test_a_barrel_waters_the_squares_beside_the_line_by_gravity_without_loss(self):
        lua = self.bench("clean")
        self.assertEqual(dict(lua.eval("FARM.watered").items()), {"2,1": 2, "4,0": 1})
        # ADR-006 D01: three line squares draw 0.5 L each (DripFlow), 1.5 L whatever the plants need (was 0.6 L)
        self.assertAlmostEqual(lua.eval('CONT["0,-1"].amount'), 28.5)
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.outlet.state"), "served")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "170")

    def test_the_flow_option_sets_what_each_square_draws(self):
        # 0.2 L a square: the square beside the thirsty plant gives it one dose only
        lua = self.bench("clean", "SCALE.DripFlow = 0.2")
        self.assertEqual(dict(lua.eval("FARM.watered").items()), {"2,1": 1, "4,0": 1})
        self.assertAlmostEqual(lua.eval('CONT["0,-1"].amount'), 29.4)

    def test_no_thirsty_plant_still_draws_the_flow(self):
        lua = services(new_lua, FITTING, DRIP)
        lua.execute(BENCH)
        lua.execute('CONT["0,-1"] = { amount = 30, capacity = 400, fluid = "clean" } tick()')
        self.assertAlmostEqual(lua.eval('CONT["0,-1"].amount'), 28.5)
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.outlet.state"), "served")

    def test_tainted_barrel_water_waters_the_crops_too(self):
        lua = self.bench("tainted")
        self.assertEqual(dict(lua.eval("FARM.watered").items()), {"2,1": 2, "4,0": 1})
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.outlet.state"), "served")


def recipe():
    sys.path.insert(0, os.path.join(ROOT, "source", "tiles"))
    try:
        import build_livewater_tiles
    finally:
        sys.path.pop(0)
    return build_livewater_tiles


class DripTiles(unittest.TestCase):
    def test_the_part_and_the_tile_recipe_agree(self):
        tiles = recipe()
        self.assertEqual(tiles.TOTAL, 256)
        groups = {g["key"]: g["indices"] for g in tiles.tile_groups()}
        lua = new_lua(API, DRIP)
        for m in range(16):
            self.assertEqual(groups["drip_m%02d" % m], [160 + m])
            self.assertEqual(lua.eval('LiveWater.Parts:sprite("LiveWater:DripLine", %d)' % m), TILE + str(160 + m))
            props = tiles.tile_props(160 + m)
            self.assertEqual((props["CustomItem"], props["CustomName"], props["PickUpWeight"]),
                             ("Base.Mov_LiveWater_DripLine", "Drip Line", "2"))
            self.assertNotIn("PickUpTool", props)
            self.assertNotIn("PlaceTool", props)
            self.assertNotIn("Facing", props)


class Texts(unittest.TestCase):
    def test_moveable_recipe_and_translations(self):
        with open(os.path.join(MEDIA, "scripts", "LWT_moveables.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"item Mov_LiveWater_DripLine\s*\{[^}]*Weight = 0\.2,[^}]*"
                                       r"WorldObjectSprite = batman_livewater_01_170,")
        with open(os.path.join(MEDIA, "scripts", "LWT_recipes.txt"), encoding="ascii") as f:
            text = f.read()
        self.assertRegex(text, r"(?s)craftRecipe LWTMakeDripLine\s*\{.*?category = LiveWater,.*?item 1 \[Base\.RubberHose\],"
                               r".*?item 2 \[Base\.DuctTape\],.*?tags\[base:sharpknife\] mode:keep.*?"
                               r"item 4 Base\.Mov_LiveWater_DripLine,")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in LANGS:
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            self.assertIn("LWTMakeDripLine", load("Recipes.json"), lang)
            self.assertIn("Base.Mov_LiveWater_DripLine", load("ItemName.json"), lang)
            self.assertIn("Live_Water_Drip_Line", load("Moveables.json"), lang)
            ui = load("IG_UI.json")
            for s in ("served", "idle", "no_water", "no_pressure", "closed", "wrong_fluid"):
                self.assertIn("IGUI_LWT_Drip_" + s, ui, lang)


if __name__ == "__main__":
    unittest.main()
