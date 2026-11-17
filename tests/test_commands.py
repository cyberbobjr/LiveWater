"""E07: client commands checked on the authority (ADR-001 Q01, D10): one dispatcher with a handler table, laying
a part that is laid with an item (pipe section), dismantling it with its tool (pipe wrench); every argument and
condition re-checked, every refusal told to the player by a translation key; item and recipe scripts."""
import json
import os
import re
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")

SETUP = r"""
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS })
CMDS:register("lay", require("LiveWater/Commands/LWT_CmdLay"))
CMDS:register("dismantle", require("LiveWater/Commands/LWT_CmdDismantle"))
P = newPlayer(0, 0, 0, { ["Test.Section"] = 2 }, { ["base:pipewrench"] = true })
function lay(x, y, z, part) return CMDS:dispatch(P, "lay", { x = x, y = y, z = z or 0, part = part or "Test:Pipe" }) end
function dismantle(x, y, z) return CMDS:dispatch(P, "dismantle", { x = x, y = y, z = z or 0 }) end
"""


def bench(pump_ports=None):
    lua = services(new_lua, pump_ports=pump_ports)
    lua.execute(SETUP)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


def told(lua):
    t = lua.eval("P.told")
    return [t[i] for i in range(1, len(t) + 1)]


class Dispatcher(unittest.TestCase):
    def test_the_handler_of_the_command_name_runs_with_args_or_an_empty_table(self):
        lua = bench()
        lua.execute("""
        SEEN = {}
        CMDS:register("probe", function(ctx, player, args) SEEN.ctx, SEEN.player, SEEN.args = ctx, player, args return true end)
        OK = CMDS:dispatch(P, "probe", nil)
        """)
        self.assertTrue(lua.eval("OK"))
        self.assertTrue(lua.eval("SEEN.player == P and type(SEEN.args) == 'table' and SEEN.ctx.topology == TOPO"))

    def test_unknown_command_is_refused(self):
        lua = bench()
        self.assertEqual(call(lua, 'CMDS:dispatch(P, "explode", {})'), (False, "unknown_command"))

    def test_a_handler_registered_twice_or_not_a_function_is_refused(self):
        lua = bench()
        self.assertEqual(call(lua, 'CMDS:register("lay", function() end)'), (False, "duplicate_command"))
        self.assertEqual(call(lua, 'CMDS:register("x", 3)'), (False, "invalid_handler"))

    def test_every_refusal_reason_has_a_translation_in_en_and_fr(self):
        lua = bench()
        keys = lua.eval("Commands.REASONS")
        names = list(keys.keys())
        self.assertIn("too_far", names)
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            with open(os.path.join(tr, lang, "IG_UI.json"), encoding="utf-8") as f:
                strings = json.load(f)
            for name in names:
                self.assertIn(keys[name], strings, "%s %s" % (lang, name))
            self.assertIn(lua.eval("Commands.GENERIC"), strings)


class Lay(unittest.TestCase):
    def test_laying_consumes_one_section_and_places_the_part(self):
        lua = bench()
        self.assertTrue(lua.eval("lay(1, 0)"))
        self.assertEqual(lua.eval('P.items["Test.Section"]'), 1)
        self.assertEqual(lua.eval("REG:at(1, 0, 0).type"), "Test:Pipe")
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), "t_pipe_0")
        lua.execute("lay(2, 0)")
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), "t_pipe_2")
        self.assertEqual(told(lua), [])

    def assertRefused(self, lua, expr, reason):
        self.assertEqual(call(lua, expr), (False, reason))
        self.assertEqual(lua.eval('P.items["Test.Section"]'), 2)
        self.assertEqual(told(lua)[-1], lua.eval("Commands.REASONS[%r]" % reason))

    def test_invalid_arguments(self):
        lua = bench()
        for expr in ('CMDS:dispatch(P, "lay", { x = 1.5, y = 0, z = 0, part = "Test:Pipe" })',
                     'CMDS:dispatch(P, "lay", { x = "1", y = 0, z = 0, part = "Test:Pipe" })',
                     'CMDS:dispatch(P, "lay", { x = 1, y = 0, z = 0 })'):
            self.assertRefused(lua, expr, "invalid")

    def test_a_part_that_is_not_laid_with_an_item_or_unknown(self):
        lua = bench()
        self.assertRefused(lua, 'lay(1, 0, 0, "Test:Pump")', "not_layable")
        self.assertRefused(lua, 'lay(1, 0, 0, "Gone:Pipe")', "not_layable")

    def test_too_far_or_on_another_floor(self):
        lua = bench()
        self.assertRefused(lua, "lay(4, 0)", "too_far")
        self.assertRefused(lua, "lay(1, 0, 1)", "too_far")
        self.assertTrue(lua.eval("lay(3, -3)"))

    def test_square_not_loaded_not_free_or_occupied(self):
        lua = bench()
        lua.execute('WORLD.unloaded["1,0,0"] = true WORLD.blocked["0,1,0"] = true')
        self.assertRefused(lua, "lay(1, 0)", "not_loaded")
        self.assertRefused(lua, "lay(0, 1)", "blocked")
        lua.execute('place("Test:Spr", -1, 0)')
        self.assertRefused(lua, "lay(-1, 0)", "occupied")

    def test_no_section_in_the_inventory(self):
        lua = bench()
        lua.execute('P.items["Test.Section"] = 0')
        self.assertEqual(call(lua, "lay(1, 0)"), (False, "no_item"))
        self.assertIsNone(lua.eval("REG:at(1, 0, 0)"))

    def test_beyond_the_ports_of_a_pump(self):
        lua = bench(pump_ports=1)
        lua.execute('place("Test:Pump", 0, 0) lay(1, 0)')
        self.assertEqual(call(lua, "lay(-1, 0)"), (False, "ports_full"))
        self.assertEqual(lua.eval('P.items["Test.Section"]'), 1)
        self.assertIsNone(lua.eval("WORLD:sprite(-1, 0, 0)"))


class Dismantle(unittest.TestCase):
    def test_dismantling_returns_the_section_and_removes_the_part(self):
        lua = bench()
        lua.execute("lay(1, 0) lay(2, 0)")
        self.assertTrue(lua.eval("dismantle(2, 0)"))
        self.assertEqual(lua.eval('P.items["Test.Section"]'), 1)
        self.assertIsNone(lua.eval("REG:at(2, 0, 0)"))
        self.assertIsNone(lua.eval("WORLD:sprite(2, 0, 0)"))
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), "t_pipe_0")

    def test_refusals(self):
        lua = bench()
        lua.execute('lay(1, 0) place("Test:Pump", -1, 0)')
        self.assertEqual(call(lua, "dismantle(0, 1)"), (False, "nothing_here"))
        self.assertEqual(call(lua, "dismantle(-1, 0)"), (False, "not_layable"))
        self.assertEqual(call(lua, 'CMDS:dispatch(P, "dismantle", { x = 1, y = 0 })'), (False, "invalid"))
        lua.execute("P.x = 10")
        self.assertEqual(call(lua, "dismantle(1, 0)"), (False, "too_far"))
        lua.execute('P.x = 0 P.tools["base:pipewrench"] = nil')
        self.assertEqual(call(lua, "dismantle(1, 0)"), (False, "need_tool"))
        self.assertEqual(lua.eval("REG:at(1, 0, 0).type"), "Test:Pipe")
        self.assertEqual(told(lua)[-1], lua.eval("Commands.REASONS.need_tool"))


MENU = r"""
SENT = {}
function sendClientCommand(player, module, command, args) table.insert(SENT, { module, command, args }) end
function getItemNameFromFullType(t) return "<" .. t .. ">" end
function getText(key, a) return key .. "|" .. tostring(a) end
function getSpecificPlayer(n) return MENU_PLAYER end
local function square(sprites)
    local sq = {}
    function sq:getX() return 4 end
    function sq:getY() return 5 end
    function sq:getZ() return 0 end
    function sq:getObjects()
        return { size = function() return #sprites end,
                 get = function(_, i) return { getSpriteName = function() return sprites[i + 1] end } end }
    end
    return sq
end
function click(sprites, items)
    MENU_PLAYER = { getInventory = function() return { containsTypeRecurse = function(_, t) return items[t] == true end } end }
    local sq = square(sprites)
    OPTIONS = {}
    local context = { addOption = function(self, text, target, fn, ...) table.insert(OPTIONS, { text = text, run = function(...) fn(target, ...) end, args = { ... } }) end }
    fire("OnFillWorldObjectContextMenu", 0, context, { { getSquare = function() return sq end } }, false)
end
"""


class Menu(unittest.TestCase):
    def menu(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", "shared/LiveWater/Parts/LWT_PartPipe.lua",
                      "client/LiveWater/LWT_PipeMenu.lua")
        lua.execute(MENU)
        return lua

    def test_lay_offered_with_a_section_and_sends_the_command(self):
        lua = self.menu()
        lua.execute('click({ "floors_01_0" }, { ["LiveWater.PipeSection"] = true })')
        self.assertEqual(lua.eval("#OPTIONS"), 1)
        self.assertEqual(lua.eval("OPTIONS[1].text"), "ContextMenu_LWT_Lay|<LiveWater.PipeSection>")
        lua.execute("OPTIONS[1].run(unpack(OPTIONS[1].args))")
        self.assertEqual((lua.eval("SENT[1][1]"), lua.eval("SENT[1][2]")), ("LiveWater", "lay"))
        a = lua.eval("SENT[1][3]")
        self.assertEqual((a.x, a.y, a.z, a.part), (4, 5, 0, "LiveWater:PipeGalvanized"))

    def test_dismantle_offered_on_a_pipe_and_nothing_without_a_section(self):
        lua = self.menu()
        lua.execute('click({ "floors_01_0", "batman_livewater_01_5" }, {})')
        self.assertEqual(lua.eval("#OPTIONS"), 1)
        self.assertEqual(lua.eval("OPTIONS[1].text"), "ContextMenu_LWT_Dismantle|<LiveWater.PipeSection>")
        lua.execute('click({ "floors_01_0" }, {})')
        self.assertEqual(lua.eval("#OPTIONS"), 0)


def script(name):
    with open(os.path.join(MEDIA, "scripts", name), encoding="ascii") as f:
        return f.read()


def block(text, head):
    start = text.index(head)
    depth, i = 0, text.index("{", start)
    while True:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1


class Scripts(unittest.TestCase):
    def test_pipe_section_item(self):
        text = script("LWT_items.txt")
        self.assertRegex(text, r"^module LiveWater\b")
        item = block(text, "item PipeSection")
        self.assertRegex(item, r"Icon\s*=\s*LWT_PipeSection,")
        self.assertRegex(item, r"ItemType\s*=\s*base:normal,")

    def test_recipe_cuts_a_metal_pipe_into_four_sections_with_a_hacksaw(self):
        text = script("LWT_recipes.txt")
        self.assertRegex(text, r"^module LiveWater\b")
        recipe = block(text, "craftRecipe LWTCutPipeSections")
        self.assertRegex(recipe, r"item 1 \[Base\.MetalPipe\]")
        self.assertRegex(recipe, r"item 1 tags\[base:metalsaw\] mode:keep")
        self.assertRegex(recipe, r"item 4 LiveWater\.PipeSection,")

    def test_names_translated_in_en_and_fr(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            with open(os.path.join(tr, lang, "ItemName.json"), encoding="utf-8") as f:
                self.assertIn("LiveWater.PipeSection", json.load(f))
            with open(os.path.join(tr, lang, "Recipes.json"), encoding="utf-8") as f:
                self.assertIn("LWTCutPipeSections", json.load(f))


if __name__ == "__main__":
    unittest.main()
