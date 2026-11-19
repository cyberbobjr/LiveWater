"""E10: water filter cartridge (ADR-001 D17, Q02, P07; ADR-005 D01, D04): LiveWater.WaterFilter made from charcoal and
cloth, 500 L per cartridge (sandbox multiplier), fitted into and taken out of the house water inlet by server commands,
the inlet sprite shows it (green while it cleans, amber once worn), it wears by the litres the house takes; a worn
cartridge comes back as LiveWater.WaterFilterSpent (ADR-009 D01), recharged by a recipe (D02), a partly used one comes back
with its condition."""
import json
import os
import re
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
INLET = "shared/LiveWater/Parts/LWT_PartHouseInlet.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"
FILTER = "LiveWater.WaterFilter"
SPENT = "LiveWater.WaterFilterSpent"

BENCH = r"""
LiveWater.API.registerPart("Test:Spr", { sprites = { [0] = "t_spr" }, capabilities = { outlet = { type = "sprinkler" } } })
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
    lua = services(new_lua, POND, INLET)
    lua.execute(BENCH)
    lua.execute('place("LiveWater:PondPump", 0, 0, "%s26") place("LiveWater:HouseInlet", 1, 0, "%s40")'
                ' place("Test:Spr", 0, -1)' % (TILE, TILE))
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


def delivered(lua, x):
    """Litres and quality delivered to the outlet at (x, 0) by the last step, or None."""
    for d in lua.eval('emitted("waterDelivered")').values():
        if d[2].x == x:
            return d[3], d[4]
    return None


class Filtering(unittest.TestCase):
    def test_without_a_cartridge_the_house_gets_no_tainted_water_and_the_inlet_turns_amber(self):
        lua = bench()
        lua.execute('NEED["1,0"] = 10 EMITTED = {} CLOCK:tick()')
        self.assertIsNone(delivered(lua, 1))
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "44")

    def test_a_cartridge_fitted_in_the_inlet_cleans_the_house_water_and_wears_by_volume(self):
        lua = bench()
        self.assertTrue(lua.eval('cmd("fitFilter", 1, 0)'))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 1)
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "176")
        lua.execute('NEED["1,0"] = 40 EMITTED = {} CLOCK:tick()')
        self.assertEqual(delivered(lua, 1), (40, "clean"))
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 40)
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "176")

    def test_the_sprinkler_takes_the_tainted_water_without_wearing_the_cartridge(self):
        lua = bench()
        lua.execute('cmd("fitFilter", 1, 0) NEED["0,-1"] = 10 EMITTED = {} CLOCK:tick()')
        self.assertEqual(delivered(lua, 0), (10, "tainted"))
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 0)

    def test_a_worn_cartridge_stops_cleaning_and_the_inlet_shows_it_amber(self):
        lua = bench()
        lua.execute('cmd("fitFilter", 1, 0) REG:at(1, 0, 0).data.filter.used = 500')
        lua.execute('NEED["1,0"] = 10 EMITTED = {} CLOCK:tick()')
        self.assertIsNone(delivered(lua, 1))
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "180")

    def test_capacity_follows_the_sandbox_multiplier(self):
        lua = bench()
        lua.execute('SCALE = function(n) return n == "FilterCapacityMultiplier" and 0.1 or 1 end'
                    ' CLOCK.ctx.scale = SCALE CMDS.ctx.scale = SCALE')
        lua.execute('cmd("fitFilter", 1, 0) NEED["1,0"] = 50 CLOCK:tick() EMITTED = {} CLOCK:tick()')
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 50)
        self.assertIsNone(delivered(lua, 1))


class FilterCommands(unittest.TestCase):
    def test_a_partly_used_cartridge_comes_back_with_its_condition(self):
        lua = bench()
        lua.execute('cmd("fitFilter", 1, 0) REG:at(1, 0, 0).data.filter.used = 125')
        self.assertTrue(lua.eval('cmd("removeFilter", 1, 0)'))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 2)
        self.assertEqual(lua.eval("P.given[1].fraction"), 0.75)
        self.assertFalse(lua.eval("REG:at(1, 0, 0).data.filter.fitted"))
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + "40")

    def test_a_worn_cartridge_comes_back_spent(self):
        lua = bench()
        lua.execute('cmd("fitFilter", 1, 0) REG:at(1, 0, 0).data.filter.used = 500')
        self.assertTrue(lua.eval('cmd("removeFilter", 1, 0)'))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 1)
        self.assertEqual(lua.eval('P.items["%s"]' % SPENT), 1)
        self.assertEqual(lua.eval("P.given[1].type"), SPENT)
        self.assertIsNone(lua.eval("P.given[1].fraction"))
        self.assertFalse(lua.eval("REG:at(1, 0, 0).data.filter.fitted"))

    def test_replacing_a_worn_cartridge_gives_the_spent_one_back(self):
        lua = bench()
        lua.execute('cmd("fitFilter", 1, 0) REG:at(1, 0, 0).data.filter.used = 500')
        self.assertTrue(lua.eval('cmd("fitFilter", 1, 0)'))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 0)
        self.assertEqual(lua.eval("P.given[1].type"), SPENT)
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 0)

    def test_a_spent_cartridge_is_never_fitted(self):
        lua = bench()
        lua.execute('P.items = { ["%s"] = 1 }' % SPENT)
        self.assertEqual(call(lua, 'cmd("fitFilter", 1, 0)'), (False, "no_cartridge"))
        self.assertEqual(lua.eval('P.items["%s"]' % SPENT), 1)
        self.assertFalse(lua.eval("REG:at(1, 0, 0).data.filter and REG:at(1, 0, 0).data.filter.fitted or false"))

    def test_a_used_cartridge_keeps_its_wear_and_replacing_returns_the_old_one(self):
        lua = bench()
        lua.execute('P.fractions = { ["LiveWater.WaterFilter"] = 0.5 } cmd("fitFilter", 1, 0)')
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 250)
        lua.execute('P.fractions = {} cmd("fitFilter", 1, 0)')
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 0)
        self.assertEqual(lua.eval("P.given[1].fraction"), 0.5)

    def test_refusals(self):
        lua = bench()
        self.assertEqual(call(lua, 'cmd("removeFilter", 1, 0)'), (False, "no_filter"))
        self.assertEqual(call(lua, 'cmd("fitFilter", 0, 0)'), (False, "no_filter_slot"))
        self.assertEqual(call(lua, 'cmd("fitFilter", 9, 9)'), (False, "nothing_here"))
        lua.execute("P.x = 10")
        self.assertEqual(call(lua, 'cmd("fitFilter", 1, 0)'), (False, "too_far"))
        lua.execute('P.x = 0 P.items["LiveWater.WaterFilter"] = 0')
        self.assertEqual(call(lua, 'cmd("fitFilter", 1, 0)'), (False, "no_cartridge"))
        self.assertEqual(lua.eval("P.told[#P.told]"), "IGUI_LWT_NoFilter")


MENU = r"""
SENT = {}
function sendClientCommand(player, module, command, args) table.insert(SENT, { module, command, args }) end
function getText(key, a) return key end
function getItemNameFromFullType(t) return "<" .. t .. ">" end
ISToolTip = { new = function() return { initialise = function() end, setName = function() end } end }
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
        lua = new_lua("shared/LiveWater/LWT_API.lua", INLET, "client/LiveWater/LWT_PartMenu.lua")
        lua.execute(MENU)
        return lua

    def test_fit_offered_with_a_cartridge_then_remove_and_replace(self):
        lua = self.menu()
        lua.execute('STATE = { type = "LiveWater:HouseInlet", data = {} } click({ "%s40" }, { [%r] = true })' % (TILE, FILTER))
        self.assertIn("ContextMenu_LWT_FitFilter", list(lua.eval("texts()").values()))
        option = [o for o in lua.eval("OPTIONS").values() if o.text == "ContextMenu_LWT_FitFilter"][0]
        lua.globals().OPT = option
        lua.execute("OPT.run(unpack(OPT.args))")
        self.assertEqual(lua.eval("SENT[1][2]"), "fitFilter")
        self.assertEqual((lua.eval("SENT[1][3].x"), lua.eval("SENT[1][3].y")), (4, 5))
        lua.execute('STATE = { type = "LiveWater:HouseInlet", data = { filter = { fitted = true, used = 0 } } }'
                    ' click({ "%s176" }, {})' % TILE)
        texts = list(lua.eval("texts()").values())
        self.assertIn("ContextMenu_LWT_RemoveFilter", texts)
        self.assertNotIn("ContextMenu_LWT_ReplaceFilter", texts)
        lua.execute('click({ "%s176" }, { [%r] = true })' % (TILE, FILTER))
        self.assertIn("ContextMenu_LWT_ReplaceFilter", list(lua.eval("texts()").values()))

    def test_fit_not_offered_without_a_cartridge_on_an_empty_inlet(self):
        lua = self.menu()
        lua.execute('STATE = { type = "LiveWater:HouseInlet", data = {} } click({ "%s40" }, {})' % TILE)
        texts = list(lua.eval("texts()").values())
        for key in ("ContextMenu_LWT_FitFilter", "ContextMenu_LWT_ReplaceFilter", "ContextMenu_LWT_RemoveFilter"):
            self.assertNotIn(key, texts)


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
        self.assertRegex(script("LWT_items.txt"), r"item WaterFilterSpent\s*\{[^}]*Icon\s*=\s*LWT_WaterFilterSpent,")
        self.assertNotRegex(script("LWT_items.txt"), r"item WaterFilterSpent\s*\{[^}]*ConditionMax")
        recharge = re.search(r"craftRecipe LWTRechargeWaterFilter\s*\{[\s\S]*?outputs[\s\S]*?\}",
                             script("LWT_recipes.txt")).group(0)
        make = re.search(r"craftRecipe LWTMakeWaterFilter\s*\{([\s\S]*?)inputs", script("LWT_recipes.txt")).group(1)
        fields = r"\n\s*(\w+ = [^\n]+)"
        self.assertEqual(re.findall(fields, re.search(r"\{([\s\S]*?)inputs", recharge).group(1)),
                         re.findall(fields, make))
        ins = re.search(r"inputs\s*\{([^}]*)\}", recharge).group(1)
        self.assertEqual([l.strip() for l in ins.strip().splitlines()],
                         ["item 1 [%s] mode:destroy," % SPENT, "item 2 tags[base:charcoal],",
                          "item 1 [Base.RippedSheets] mode:destroy,"])
        self.assertRegex(re.search(r"outputs\s*\{([^}]*)\}", recharge).group(1), r"^\s*item 1 LiveWater\.WaterFilter,\s*$")
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
            self.assertIn(SPENT, load("ItemName.json"))
            self.assertIn("LWTRechargeWaterFilter", load("Recipes.json"))
            self.assertIn("Tooltip_LWT_WaterFilter", load("Tooltip.json"))
            for key in ("ContextMenu_LWT_FitFilter", "ContextMenu_LWT_ReplaceFilter", "ContextMenu_LWT_RemoveFilter"):
                self.assertIn(key, load("ContextMenu.json"))
            for key in ("IGUI_LWT_NoFilter", "IGUI_LWT_NoFilterFitted", "IGUI_LWT_NoFilterSlot", "IGUI_LWT_Filter_Left",
                        "IGUI_LWT_Filter_Worn", "IGUI_LWT_Filter_None"):
                self.assertIn(key, load("IG_UI.json"))
            self.assertIn("Sandbox_LWT_FilterCapacityMultiplier", load("Sandbox.json"))


if __name__ == "__main__":
    unittest.main()
