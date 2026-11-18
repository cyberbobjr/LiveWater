"""E20: barrel fitting (ADR-001 D26, P02, P17): part LiveWater:BarrelFitting set between a pipe and a barrel, "Fill"
(outlet: the network fills the barrel, no leak) or "Pump" (source: the pumps draw the barrel's content instead of
their intake); sprite by mode and by the shape of the container (data table, extendable through the API, unknown =
tall); one fluid per network: a fuel network serves only fittings set to Fill whose barrel is empty or holds fuel."""
import json
import os
import unittest

from lwt_fakes import services
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
        for key, base in (("fill", 64), ("fill_low", 68), ("pump", 72)):
            self.assertEqual([d.variants[key][i] for i in range(1, 5)], [TILE + str(base + k) for k in range(4)], key)
        self.assertEqual(d.capabilities.fitting.rate, 50)
        self.assertGreaterEqual(lua.eval("LiveWater.API.revision"), 11)

    def test_the_look_follows_the_mode_and_the_shape(self):
        lua = new_lua(API, FITTING)
        lua.execute('P = { type = "LiveWater:BarrelFitting", data = {} }')
        self.assertEqual(lua.eval("LiveWater.Parts:look(P)"), "fill")
        lua.execute('LiveWater.Parts:call(P, "sense", { found = true, shape = "low", amount = 0, free = 400 })')
        self.assertEqual(lua.eval("LiveWater.Parts:look(P)"), "fill_low")
        lua.execute('LiveWater.Parts:call(P, "setFittingMode", "pump")')
        self.assertEqual(lua.eval("LiveWater.Parts:look(P)"), "pump")


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


BENCH = r"""
CONT = {}
CONTAINERS = {}
function CONTAINERS:at(x, y, z)
    local c = CONT[x .. "," .. y]
    if not c then return nil end
    return { fluid = c.amount > 0 and c.fluid or nil, amount = c.amount, free = c.capacity - c.amount, sprite = c.sprite }
end
function CONTAINERS:add(x, y, z, litres, quality)
    local c = CONT[x .. "," .. y]
    c.amount = c.amount + litres
    c.fluid = quality
    return litres
end
function CONTAINERS:take(x, y, z, litres)
    local c = CONT[x .. "," .. y]
    c.amount = c.amount - litres
    return litres
end
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
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "64")

    def test_a_low_crate_collector_draws_the_low_sprite(self):
        lua = bench()
        lua.execute('CONT["2,-1"] = { amount = 0, capacity = 400, sprite = "carpentry_02_54" } tick()')
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "68")

    def test_no_leak_a_full_barrel_or_none_takes_nothing(self):
        lua = bench()
        lua.execute('CONT["2,-1"] = { amount = 400, capacity = 400, fluid = "clean" } tick()')
        self.assertEqual(lua.eval('state(2, 0)'), "idle")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 400)
        lua.execute('CONT["2,-1"] = nil tick()')
        self.assertEqual(lua.eval('state(2, 0)'), "idle")
        lines = [l[1] for l in lua.eval("LiveWater.Parts:lines(FIT)").values()]
        self.assertIn("IGUI_LWT_Fitting_NoBarrel", lines)


class Pump(unittest.TestCase):
    def test_the_pumps_draw_the_barrel_instead_of_their_intake(self):
        lua = bench()
        lua.execute(r"""
        place("Test:Spr", 1, 1) NEED["1,1"] = 20
        CONT["2,-1"] = { amount = 30, capacity = 600, fluid = "clean" }
        LiveWater.Parts:call(FIT, "setFittingMode", "pump")
        tick()
        """)
        d = lua.eval('emitted("waterDelivered")')
        self.assertEqual((d[1][3], d[1][4]), (20, "clean"))
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 10)
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "72")
        self.assertTrue(lua.eval("REG:at(0, 0, 0).data.pump.running"))
        self.assertEqual(lua.eval('#emitted("waterDrawn")'), 1)

    def test_an_empty_barrel_leaves_the_pump_on_its_intake(self):
        lua = bench()
        lua.execute(r"""
        place("Test:Spr", 1, 1) NEED["1,1"] = 20
        CONT["2,-1"] = { amount = 0, capacity = 600 }
        LiveWater.Parts:call(FIT, "setFittingMode", "pump") tick()
        """)
        d = lua.eval('emitted("waterDelivered")')
        self.assertEqual((d[1][3], d[1][4]), (20, "tainted"))


FUEL = r"""
LiveWater.Parts:call(FIT, "setFittingMode", "pump")
CONT["2,-1"] = { amount = 100, capacity = 600, fluid = "fuel" }
place("LiveWater:BarrelFitting", 1, 1, "batman_livewater_01_66")
CONT["1,2"] = { amount = 0, capacity = 400 }
place("Test:Spr", 0, 1) NEED["0,1"] = 10
"""


class Fuel(unittest.TestCase):
    def test_a_fuel_network_fills_only_the_fittings_set_to_fill(self):
        lua = bench()
        lua.execute(FUEL)
        lua.execute("tick()")
        self.assertEqual(lua.eval('state(1, 1)'), "served")
        self.assertEqual(lua.eval('CONT["1,2"].fluid'), "fuel")
        self.assertEqual(lua.eval('CONT["1,2"].amount'), 50)
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 50)
        self.assertEqual(lua.eval('REG:at(0, 1, 0).data.outlet.state'), "wrong_fluid")

    def test_a_barrel_holding_water_refuses_fuel(self):
        lua = bench()
        lua.execute(FUEL)
        lua.execute('CONT["1,2"] = { amount = 10, capacity = 400, fluid = "clean" } tick()')
        self.assertEqual(lua.eval('state(1, 1)'), "wrong_fluid")
        self.assertEqual(lua.eval('CONT["1,2"].amount'), 10)


COMMAND = r"""
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS,
    publisher = { present = function() end } })
CMDS:register("switchFitting", require("LiveWater/Commands/LWT_CmdSwitchFitting"))
P = newPlayer(2, 1, 0)
place("LiveWater:BarrelFitting", 2, 0, "batman_livewater_01_64")
place("Test:Pipe", 3, 0)
function cmd(x) return CMDS:dispatch(P, "switchFitting", { x = x, y = 0, z = 0 }) end
"""


class SwitchCommand(unittest.TestCase):
    def test_fill_and_pump_alternate_and_refusals(self):
        lua = services(new_lua, FITTING)
        lua.execute(COMMAND)
        self.assertTrue(lua.eval("cmd(2)"))
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.fitting.mode"), "pump")
        self.assertTrue(lua.eval("cmd(2)"))
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.fitting.mode"), "fill")
        self.assertEqual(call(lua, "cmd(3)"), (False, "not_fitting"))
        lua.execute("P.x = 9")
        self.assertEqual(call(lua, "cmd(2)"), (False, "too_far"))

    def test_the_menu_action_follows_the_mode(self):
        lua = new_lua(API, FITTING)
        a = lua.eval('LiveWater.Parts:actions({ type = "LiveWater:BarrelFitting", data = {} })')
        self.assertEqual((a[1].command, a[1].key), ("switchFitting", "ContextMenu_LWT_FittingToPump"))


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
            menu, ui = load("ContextMenu.json"), load("IG_UI.json")
            for key in ("ContextMenu_LWT_FittingToPump", "ContextMenu_LWT_FittingToFill"):
                self.assertIn(key, menu, lang)
            for key in ("IGUI_LWT_Fitting_fill", "IGUI_LWT_Fitting_pump", "IGUI_LWT_Fitting_NoBarrel",
                        "IGUI_LWT_Fitting_wrong_fluid", "IGUI_LWT_Outlet_wrong_fluid", "IGUI_LWT_Sprinkler_wrong_fluid",
                        "IGUI_LWT_Fluid_fuel", "IGUI_LWT_Fitting_Content"):
                self.assertIn(key, ui, lang)
            self.assertIn("LWTBuildBarrelFitting", load("Recipes.json"), lang)


if __name__ == "__main__":
    unittest.main()
