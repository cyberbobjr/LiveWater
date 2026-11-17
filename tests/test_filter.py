"""E10: water filter cartridge (ADR-001 D17, Q02, P07): LiveWater.WaterFilter made from charcoal and cloth, 500 L per
cartridge (sandbox multiplier), fitted into and taken out of the pond pump by server commands, the pump sprite shows
it, it wears by volume; a worn cartridge is thrown away, a partly used one comes back with its condition."""
import json
import os
import re
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"
FILTER = "LiveWater.WaterFilter"

BENCH = r"""
LiveWater.API.registerPart("Test:Inlet", { sprites = { [0] = "t_inlet" },
    capabilities = { outlet = { type = "houseInlet" } } })
POWER = { powered = function() return true end }
NEED = {}
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, power = POWER, publisher = PUB,
    need = function(part) return NEED[part.x .. "," .. part.y] or 0 end })
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS, publisher = PUB })
CMDS:register("fitFilter", require("LiveWater/Commands/LWT_CmdFitFilter"))
CMDS:register("removeFilter", require("LiveWater/Commands/LWT_CmdRemoveFilter"))
P = newPlayer(0, 1, 0, { ["LiveWater.WaterFilter"] = 2 })
function cmd(name, x, y) return CMDS:dispatch(P, name, { x = x or 0, y = y or 0, z = 0 }) end
"""


def bench():
    lua = services(new_lua, POND)
    lua.execute(BENCH)
    lua.execute('place("LiveWater:PondPump", 0, 0, "%s26") place("Test:Inlet", 1, 0)' % TILE)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Filtering(unittest.TestCase):
    def test_without_a_cartridge_the_house_gets_no_tainted_water(self):
        lua = bench()
        lua.execute('NEED["1,0"] = 10 EMITTED = {} CLOCK:tick()')
        self.assertEqual(len(lua.eval('emitted("waterDelivered")')), 0)

    def test_a_fitted_cartridge_cleans_the_water_and_wears_by_volume(self):
        lua = bench()
        self.assertTrue(lua.eval('cmd("fitFilter")'))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 1)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "38")
        lua.execute('NEED["1,0"] = 40 EMITTED = {} CLOCK:tick()')
        delivered = lua.eval('emitted("waterDelivered")')
        self.assertEqual((delivered[1][3], delivered[1][4]), (40, "clean"))
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.filter.used"), 40)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "34")

    def test_a_worn_cartridge_stops_cleaning(self):
        lua = bench()
        lua.execute('cmd("fitFilter") REG:at(0, 0, 0).data.filter.used = 500')
        lua.execute('NEED["1,0"] = 10 EMITTED = {} CLOCK:tick()')
        self.assertEqual(len(lua.eval('emitted("waterDelivered")')), 0)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "38")

    def test_capacity_follows_the_sandbox_multiplier(self):
        lua = bench()
        lua.execute('SCALE = function(n) return n == "FilterCapacityMultiplier" and 0.1 or 1 end'
                    ' CLOCK.ctx.scale = SCALE CMDS.ctx.scale = SCALE')
        lua.execute('cmd("fitFilter") NEED["1,0"] = 50 CLOCK:tick() EMITTED = {} CLOCK:tick()')
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.filter.used"), 50)
        self.assertEqual(len(lua.eval('emitted("waterDelivered")')), 0)


class FilterCommands(unittest.TestCase):
    def test_a_partly_used_cartridge_comes_back_with_its_condition(self):
        lua = bench()
        lua.execute('cmd("fitFilter") REG:at(0, 0, 0).data.filter.used = 125')
        self.assertTrue(lua.eval('cmd("removeFilter")'))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 2)
        self.assertEqual(lua.eval("P.given[1].fraction"), 0.75)
        self.assertFalse(lua.eval("REG:at(0, 0, 0).data.filter.fitted"))
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "26")

    def test_a_worn_cartridge_is_thrown_away(self):
        lua = bench()
        lua.execute('cmd("fitFilter") REG:at(0, 0, 0).data.filter.used = 500')
        self.assertTrue(lua.eval('cmd("removeFilter")'))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 1)

    def test_a_used_cartridge_keeps_its_wear_and_replacing_returns_the_old_one(self):
        lua = bench()
        lua.execute('P.fractions = { ["LiveWater.WaterFilter"] = 0.5 } cmd("fitFilter")')
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.filter.used"), 250)
        lua.execute('P.fractions = {} cmd("fitFilter")')
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.filter.used"), 0)
        self.assertEqual(lua.eval("P.given[1].fraction"), 0.5)

    def test_refusals(self):
        lua = bench()
        self.assertEqual(call(lua, 'cmd("removeFilter")'), (False, "no_filter"))
        self.assertEqual(call(lua, 'cmd("fitFilter", 1, 0)'), (False, "no_filter_slot"))
        self.assertEqual(call(lua, 'cmd("fitFilter", 9, 9)'), (False, "nothing_here"))
        lua.execute("P.x = 10")
        self.assertEqual(call(lua, 'cmd("fitFilter")'), (False, "too_far"))
        lua.execute('P.x = 0 P.items["LiveWater.WaterFilter"] = 0')
        self.assertEqual(call(lua, 'cmd("fitFilter")'), (False, "no_cartridge"))
        self.assertEqual(lua.eval("P.told[#P.told]"), "IGUI_LWT_NoFilter")


MENU = r"""
SENT = {}
function sendClientCommand(player, module, command, args) table.insert(SENT, { module, command, args }) end
function getText(key, a) return key end
function getItemNameFromFullType(t) return "<" .. t .. ">" end
STATE = nil
local function object(sprite)
    return { getSpriteName = function() return sprite end,
             getModData = function() return { movableData = { LiveWater = STATE } } end }
end
function getSpecificPlayer(n) return MENU_PLAYER end
function click(sprites, items)
    MENU_PLAYER = { getInventory = function() return { containsTypeRecurse = function(_, t) return items[t] == true end } end }
    local objs = {}
    for i, s in ipairs(sprites) do objs[i] = object(s) end
    local sq = { getX = function() return 4 end, getY = function() return 5 end, getZ = function() return 0 end,
        getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
    OPTIONS = {}
    local context = { addOption = function(self, text, target, fn, ...)
        local o = { text = text, run = function(...) fn(target, ...) end, args = { ... } }
        table.insert(OPTIONS, o) return o end }
    fire("OnFillWorldObjectContextMenu", 0, context, { { getSquare = function() return sq end } }, false)
end
function texts() local out = {} for i, o in ipairs(OPTIONS) do out[i] = o.text end return out end
"""


class Menu(unittest.TestCase):
    def menu(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", POND, "client/LiveWater/LWT_PartMenu.lua")
        lua.execute(MENU)
        return lua

    def test_fit_offered_with_a_cartridge_then_remove_and_replace(self):
        lua = self.menu()
        lua.execute('STATE = { type = "LiveWater:PondPump", data = {} } click({ "%s24" }, { [%r] = true })' % (TILE, FILTER))
        self.assertIn("ContextMenu_LWT_FitFilter", list(lua.eval("texts()").values()))
        option = [o for o in lua.eval("OPTIONS").values() if o.text == "ContextMenu_LWT_FitFilter"][0]
        lua.globals().OPT = option
        lua.execute("OPT.run(unpack(OPT.args))")
        self.assertEqual(lua.eval("SENT[1][2]"), "fitFilter")
        self.assertEqual((lua.eval("SENT[1][3].x"), lua.eval("SENT[1][3].y")), (4, 5))
        lua.execute('STATE = { type = "LiveWater:PondPump", data = { filter = { fitted = true, used = 0 } } }'
                    ' click({ "%s36" }, {})' % TILE)
        self.assertEqual(list(lua.eval("texts()").values()), ["ContextMenu_LWT_RemoveFilter"])
        lua.execute('click({ "%s36" }, { [%r] = true })' % (TILE, FILTER))
        self.assertIn("ContextMenu_LWT_ReplaceFilter", list(lua.eval("texts()").values()))

    def test_nothing_without_a_cartridge_on_a_pump_without_filter(self):
        lua = self.menu()
        lua.execute('STATE = { type = "LiveWater:PondPump", data = {} } click({ "%s24" }, {})' % TILE)
        self.assertEqual(lua.eval("#OPTIONS"), 0)


def script(name):
    with open(os.path.join(MEDIA, "scripts", name), encoding="ascii") as f:
        return f.read()


class Scripts(unittest.TestCase):
    def test_item_recipe_option_and_texts(self):
        self.assertRegex(script("LWT_items.txt"), r"item WaterFilter\s*\{[^}]*Icon\s*=\s*LWT_WaterFilter,[^}]*ConditionMax = 100,")
        recipe = re.search(r"craftRecipe LWTMakeWaterFilter[\s\S]*?outputs[\s\S]*?\}", script("LWT_recipes.txt")).group(0)
        self.assertIn("tags[base:charcoal]", recipe)
        self.assertIn("[Base.RippedSheets]", recipe)
        self.assertIn("item 1 LiveWater.WaterFilter", recipe)
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"option LiveWater\.FilterCapacityMultiplier\s*\{\s*type = double, min = [\d.]+,"
                                       r" max = [\d.]+, default = 1\.0,")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            self.assertIn(FILTER, load("ItemName.json"))
            self.assertIn("LWTMakeWaterFilter", load("Recipes.json"))
            self.assertIn("Tooltip_LWT_WaterFilter", load("Tooltip.json"))
            for key in ("ContextMenu_LWT_FitFilter", "ContextMenu_LWT_ReplaceFilter", "ContextMenu_LWT_RemoveFilter"):
                self.assertIn(key, load("ContextMenu.json"))
            for key in ("IGUI_LWT_NoFilter", "IGUI_LWT_NoFilterFitted", "IGUI_LWT_NoFilterSlot", "IGUI_LWT_Filter_Left",
                        "IGUI_LWT_Filter_Worn", "IGUI_LWT_Filter_None"):
                self.assertIn(key, load("IG_UI.json"))
            self.assertIn("Sandbox_LWT_FilterCapacityMultiplier", load("Sandbox.json"))


if __name__ == "__main__":
    unittest.main()
