"""E07: client commands checked on the authority (ADR-001 D10): one dispatcher with a handler table, every refusal
told to the player by a translation key; the pipe is a moveable set down with the vanilla cursor (ADR-001 Q01
updated 2026-11-18): its item, its recipe, its tiles."""
import json
import os
import re
import sys
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")

SETUP = r"""
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS })
P = newPlayer(0, 0, 0)
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
        lua.execute('CMDS:register("probe", function() end)')
        self.assertEqual(call(lua, 'CMDS:register("probe", function() end)'), (False, "duplicate_command"))
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
    def test_the_pipe_is_a_moveable_shown_straight_on_the_cursor(self):
        text = script("LWT_moveables.txt")
        item = block(text, "item Mov_LiveWater_Pipe")
        self.assertRegex(item, r"ItemType\s*=\s*base:moveable,")
        self.assertRegex(item, r"WorldObjectSprite\s*=\s*batman_livewater_01_10,")

    def test_every_pipe_tile_gives_the_pipe_item_back(self):
        sys.path.insert(0, os.path.join(ROOT, "source", "tiles"))
        try:
            from build_livewater_tiles import tile_props
        finally:
            sys.path.pop(0)
        for mask in range(16):
            props = tile_props(mask)
            self.assertIn("IsMoveAble", props, mask)
            self.assertEqual(props.get("CustomItem"), "Base.Mov_LiveWater_Pipe", mask)
            self.assertNotIn("Facing", props, mask)

    def test_recipe_cuts_a_metal_pipe_into_four_pipes_with_a_hacksaw(self):
        text = script("LWT_recipes.txt")
        self.assertRegex(text, r"^module LiveWater\b")
        recipe = block(text, "craftRecipe LWTCutPipeSections")
        self.assertRegex(recipe, r"item 1 \[Base\.MetalPipe\]")
        self.assertRegex(recipe, r"item 1 tags\[base:metalsaw\] mode:keep")
        self.assertRegex(recipe, r"item 4 Base\.Mov_LiveWater_Pipe,")

    def test_names_translated_in_en_and_fr(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            with open(os.path.join(tr, lang, "ItemName.json"), encoding="utf-8") as f:
                self.assertIn("Base.Mov_LiveWater_Pipe", json.load(f))
            with open(os.path.join(tr, lang, "Recipes.json"), encoding="utf-8") as f:
                self.assertIn("LWTCutPipeSections", json.load(f))

if __name__ == "__main__":
    unittest.main()
