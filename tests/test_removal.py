"""E21: clean removal of LiveWater from a world (ADR-001 P21, L14, D03): an admin action removes every LiveWater part
on a loaded square (their relays and barrel connections go with them through partRemoved), the parts on squares not
loaded go when their area loads (clock chore), parts of an unknown type are kept (D03); a player who is not an admin
is refused; the client asks for a confirmation."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


BENCH = r"""
REMOVAL = require("LiveWater/LWT_Removal").new({ store = STORE, registry = REG, topology = TOPO, world = WORLD,
    log = function() end })
TOPO.closed = function() return REMOVAL:started() end
place("Test:Pump", 0, 0) place("Test:Pipe", 1, 0) place("Test:Pipe", 5, 5)
STORE.parts["9,9,0"] = { v = 1, type = "Gone:Part", x = 9, y = 9, z = 0, order = 99, data = {} }
WORLD.unloaded["5,5,0"] = true
"""


def bench():
    lua = services(new_lua)
    lua.execute(BENCH)
    return lua


class Service(unittest.TestCase):
    def test_parts_on_loaded_squares_go_the_others_wait(self):
        lua = bench()
        t = lua.eval("{ REMOVAL:start() }")
        self.assertEqual((t[1], t[2]), (2, 1))
        self.assertIsNone(lua.eval("REG:at(0, 0, 0)"))
        self.assertIsNone(lua.eval("WORLD:sprite(0, 0, 0)"))
        self.assertIsNone(lua.eval("WORLD:sprite(1, 0, 0)"))
        self.assertEqual(lua.eval('#emitted("partRemoved")'), 2)
        self.assertIsNotNone(lua.eval("REG:at(5, 5, 0)"))
        lua.execute('WORLD.unloaded["5,5,0"] = nil REMOVAL:tick()')
        self.assertIsNone(lua.eval("REG:at(5, 5, 0)"))
        self.assertTrue(lua.eval("REMOVAL:done()"))

    def test_parts_of_an_unknown_type_are_kept(self):
        lua = bench()
        lua.execute('WORLD.unloaded["5,5,0"] = nil REMOVAL:start()')
        self.assertEqual(lua.eval('STORE.parts["9,9,0"].type'), "Gone:Part")

    def test_a_part_set_down_after_the_removal_is_refused_and_never_taken_away(self):
        # No item may vanish: the tile stays a decoration the player can pick up again.
        lua = bench()
        lua.execute('WORLD.unloaded["5,5,0"] = nil REMOVAL:start()')
        self.assertEqual(call(lua, 'place("Test:Pipe", 3, 3)'), (False, "removed"))
        lua.execute("REMOVAL:tick()")
        self.assertIsNone(lua.eval("REG:at(3, 3, 0)"))
        self.assertIsNotNone(lua.eval("WORLD:sprite(3, 3, 0)"))

    def test_the_refusal_is_translated(self):
        lua = bench()
        self.assertEqual(lua.eval('require("LiveWater/LWT_Reasons").key("removed")'), "IGUI_LWT_RemovedFromWorld")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in os.listdir(tr):
            with open(os.path.join(tr, lang, "IG_UI.json"), encoding="utf-8") as f:
                self.assertIn("IGUI_LWT_RemovedFromWorld", json.load(f), lang)

    def test_nothing_happens_before_an_admin_starts_it(self):
        lua = bench()
        self.assertIsNone(lua.eval("REMOVAL:tick()"))
        self.assertIsNotNone(lua.eval("REG:at(0, 0, 0)"))


COMMAND = r"""
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS, removal = REMOVAL })
CMDS:register("removeLiveWater", require("LiveWater/Commands/LWT_CmdRemoveAll"))
function PLAYERS:isAdmin(p) return p.admin == true end
P = newPlayer(0, 0, 0)
"""


class Command(unittest.TestCase):
    def test_only_an_admin_may_remove_the_mod(self):
        lua = bench()
        lua.execute(COMMAND)
        self.assertEqual(call(lua, 'CMDS:dispatch(P, "removeLiveWater", {})'), (False, "not_admin"))
        self.assertIsNotNone(lua.eval("REG:at(0, 0, 0)"))
        lua.execute("P.admin = true")
        self.assertTrue(lua.eval('CMDS:dispatch(P, "removeLiveWater", {})'))
        self.assertIsNone(lua.eval("REG:at(0, 0, 0)"))
        self.assertEqual(lua.eval("P.told[#P.told]"), "IGUI_LWT_Removing")


MENU = r"""
SENT = {}
function sendClientCommand(player, module, command, args) table.insert(SENT, { command, args }) end
function getText(key) return key end
ALLOWED = false
PLAYER = { getRole = function() return { hasCapability = function() return ALLOWED end } end }
function getSpecificPlayer() return PLAYER end
Capability = { UseDebugContextMenu = "debug" }
function isClient() return true end
MODALS = {}
ISModalDialog = { new = function(self, x, y, w, h, text, yesno, target, onclick, a, b)
    local m = { text = text, onclick = onclick, target = target, a = a, b = b }
    function m:initialise() end
    function m:addToUIManager() table.insert(MODALS, self) end
    return m
end }
function menu()
    OPTIONS = {}
    local context = { addOption = function(self, text, target, fn, ...)
        local o = { text = text, run = function(...) fn(target, ...) end, args = { ... } }
        table.insert(OPTIONS, o) return o end }
    fire("OnFillWorldObjectContextMenu", 0, context, {}, false)
end
"""


class AdminMenu(unittest.TestCase):
    def menu(self):
        lua = new_lua(API, "client/LiveWater/LWT_AdminMenu.lua")
        lua.execute(MENU)
        return lua

    def test_hidden_from_players_offered_to_admins_with_a_confirmation(self):
        lua = self.menu()
        lua.execute("menu()")
        self.assertEqual(lua.eval("#OPTIONS"), 0)
        lua.execute("ALLOWED = true menu() OPTIONS[1].run(unpack(OPTIONS[1].args))")
        self.assertEqual(lua.eval("OPTIONS[1].text"), "ContextMenu_LWT_RemoveMod")
        self.assertEqual(lua.eval("#SENT"), 0)
        lua.execute('local m = MODALS[1] m.onclick(m.target, { internal = "NO" }, m.a, m.b)')
        self.assertEqual(lua.eval("#SENT"), 0)
        lua.execute('local m = MODALS[1] m.onclick(m.target, { internal = "YES" }, m.a, m.b)')
        self.assertEqual(lua.eval("SENT[1][1]"), "removeLiveWater")


class Texts(unittest.TestCase):
    def test_translations(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            self.assertIn("ContextMenu_LWT_RemoveMod", load("ContextMenu.json"), lang)
            for key in ("IGUI_LWT_RemoveConfirm", "IGUI_LWT_Removing", "IGUI_LWT_NotAdmin"):
                self.assertIn(key, load("IG_UI.json"), lang)


if __name__ == "__main__":
    unittest.main()
