"""E13: interface (ADR-001 D11, D14, D17): menu actions run as timed actions after walking to the square (valve, pipe
laying and dismantling...), a part the network refuses at placement is told to the player (cursor: occupied square;
authority: every refusal), and the persistent network view (highlight set when shown, cleared when hidden, colours by
the state of each outlet: no pressure, unfiltered water) with no per-frame event."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
from test_filter import MENU

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
SPRINKLER = "shared/LiveWater/Parts/LWT_PartSprinkler.lua"
INLET = "shared/LiveWater/Parts/LWT_PartHouseInlet.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class TimedActions(unittest.TestCase):
    def test_a_part_action_walks_then_sends_after_its_time(self):
        lua = new_lua(API, SPRINKLER, "client/LiveWater/LWT_PartMenu.lua")
        lua.execute(MENU)
        lua.execute('STATE = { type = "LiveWater:Sprinkler", data = {} } click({ "%s48" }, {})' % TILE)
        option = [o for o in lua.eval("OPTIONS").values() if o.text == "ContextMenu_LWT_OpenValve"][0]
        lua.globals().OPT = option
        lua.execute("OPT.run(unpack(OPT.args))")
        self.assertEqual(lua.eval("#WALKED"), 1)
        self.assertEqual(lua.eval("QUEUED[1].Type"), "LWT_PartAction")
        self.assertEqual(lua.eval("QUEUED[1].maxTime"), 60)
        self.assertEqual(lua.eval("SENT[1][2]"), "switchValve")


class PlacementRefusal(unittest.TestCase):
    def test_the_cursor_refuses_a_square_that_already_holds_a_part(self):
        lua = new_lua(API, SPRINKLER)
        lua.execute(r"""
        IsoFlagType = { water = "water" }
        function getText(k) return k end
        ISMoveableSpriteProps = { canPlaceMoveableInternal = function() return true end,
            getInfoPanelDescription = function() return {} end, addLineToInfoTable = function(t) return t end }
        RULES = require("LiveWater/LWT_PlaceRules")
        function sq(sprites)
            return { getX = function() return 1 end, getY = function() return 1 end, getZ = function() return 0 end,
                has = function() return false end,
                getObjects = function() return { size = function() return #sprites end,
                    get = function(_, i) return { getSpriteName = function() return sprites[i + 1] end } end } end }
        end
        """)
        self.assertEqual(call(lua, 'RULES.check("%s48", sq({ "floors_01_0" }))' % TILE), (True, None))
        self.assertEqual(call(lua, 'RULES.check("%s48", sq({ "%s52" }))' % (TILE, TILE)), (False, "IGUI_LWT_Occupied"))

    def test_the_authority_tells_the_players_near_why_a_part_stays_a_decoration(self):
        lua = services(new_lua, POND, pump_ports=1)
        lua.execute(r"""
        NOTES = {}
        PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function() end, WORLD,
            function(x, y, z, reason) table.insert(NOTES, { x, y, reason }) end)
        place("Test:Pump", 0, 0)
        place("Test:Pipe", 1, 0)
        WORLD:createPart(0, 1, 0, "t_pipe_0")
        OK, WHY = PLACEMENT:added("t_pipe_0", 0, 1, 0)
        """)
        self.assertEqual((lua.eval("OK"), lua.eval("WHY")), (False, "ports_full"))
        self.assertEqual(list(lua.eval("NOTES[1]").values()), [0, 1, "ports_full"])


SHOW = r"""
REPLIES = {}
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS,
    replies = { to = function(self, player, command, args) table.insert(REPLIES, { command, args }) end } })
CMDS:register("showNetwork", require("LiveWater/Commands/LWT_CmdShowNetwork"))
P = newPlayer(1, 1, 0)
place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:Pipe", 1, 0) place("Test:Spr", 2, 0)
place("Test:Pipe", 9, 9)
REG:at(2, 0, 0).data.outlet = { state = "no_pressure" }
function show(x, y) return CMDS:dispatch(P, "showNetwork", { x = x, y = y, z = 0 }) end
"""


class NetworkCommand(unittest.TestCase):
    def test_the_squares_of_the_network_go_back_to_the_player(self):
        lua = services(new_lua, POND)
        lua.execute(SHOW)
        self.assertTrue(lua.eval("show(1, 0)"))
        self.assertEqual(lua.eval("REPLIES[1][1]"), "network")
        parts = lua.eval("REPLIES[1][2].parts")
        squares = sorted((p.x, p.y) for p in parts.values())
        self.assertEqual(squares, [(0, 0), (1, 0), (2, 0)])

    def test_refusals(self):
        lua = services(new_lua, POND)
        lua.execute(SHOW)
        self.assertEqual(call(lua, "show(5, 5)"), (False, "nothing_here"))
        self.assertEqual(call(lua, "show(9, 9)"), (False, "too_far"))

    def test_the_status_hook_gives_the_state_of_an_outlet(self):
        lua = services(new_lua, POND)
        lua.execute(SHOW)
        self.assertEqual(lua.eval('(LiveWater.Parts:first(REG:at(2, 0, 0), "status"))'), "no_pressure")


VIEW = r"""
SENT = {}
function sendClientCommand(player, module, command, args) table.insert(SENT, { command, args }) end
function getText(key, a) if a ~= nil then return key .. "|" .. tostring(a) end return key end
ISToolTip = { new = function() return { initialise = function() end, setName = function() end } end }
function newObject(sprite, state)
    local o = { sprite = sprite, state = state, highlighted = false }
    o.getSpriteName = function() return o.sprite end
    o.getModData = function() return { movableData = { LiveWater = o.state } } end
    o.setHighlightColor = function(_, r, g, b, a) o.color = { r, g, b, a } end
    o.setHighlighted = function(_, on, once) o.highlighted = on o.once = once end
    return o
end
SQUARES = {}
function newSquare(x, y, objs)
    local sq = { getX = function() return x end, getY = function() return y end, getZ = function() return 0 end,
        getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
    SQUARES[x .. "," .. y] = sq
    return sq
end
function getCell() return { getGridSquare = function(_, x, y, z) return SQUARES[x .. "," .. y] end } end
PIPE = newObject("batman_livewater_01_5") newSquare(1, 0, { PIPE })
SPR = newObject("batman_livewater_01_52", { type = "LiveWater:Sprinkler", data = { outlet = { state = "no_pressure" } } })
SQ = newSquare(2, 0, { SPR })
INLET = newObject("batman_livewater_01_44", { type = "LiveWater:HouseInlet", data = { outlet = { state = "unfiltered" } } })
newSquare(3, 0, { INLET })
function getSpecificPlayer()
    return { getInventory = function() return { containsTypeRecurse = function() return false end } end }
end
function menu(sq)
    OPTIONS = {}
    local context = { addOption = function(self, text, target, fn, ...)
        local o = { text = text, run = function(...) fn(target, ...) end, args = { ... } }
        table.insert(OPTIONS, o) return o end }
    fire("OnFillWorldObjectContextMenu", 0, context, { { getSquare = function() return sq end } }, false)
end
function option(text) for _, o in ipairs(OPTIONS) do if o.text == text then return o end end end
function reply(list) fire("OnServerCommand", "LiveWater", "network", { parts = list }) end
"""


class NetworkView(unittest.TestCase):
    def view(self):
        lua = new_lua(API, "shared/LiveWater/Parts/LWT_PartPipe.lua", SPRINKLER, INLET,
                      "client/LiveWater/LWT_NetworkView.lua")
        lua.execute(VIEW)
        return lua

    def test_show_asks_the_authority_and_the_reply_highlights_by_state(self):
        lua = self.view()
        lua.execute('menu(SQ) local o = option("ContextMenu_LWT_ShowNetwork") o.run(unpack(o.args))')
        self.assertEqual(lua.eval("SENT[1][1]"), "showNetwork")
        lua.execute("reply({ { x = 1, y = 0, z = 0 }, { x = 2, y = 0, z = 0 }, { x = 3, y = 0, z = 0 } })")
        for name in ("PIPE", "SPR", "INLET"):
            self.assertTrue(lua.eval(name + ".highlighted"), name)
            self.assertFalse(lua.eval(name + ".once"), name)
        self.assertNotEqual(list(lua.eval("SPR.color").values()), list(lua.eval("PIPE.color").values()))
        self.assertNotEqual(list(lua.eval("SPR.color").values()), list(lua.eval("INLET.color").values()))

    def test_hide_clears_the_highlight_and_tells_the_states(self):
        lua = self.view()
        lua.execute("reply({ { x = 2, y = 0, z = 0 }, { x = 3, y = 0, z = 0 } }) menu(SQ)")
        hide = lua.eval('option("ContextMenu_LWT_HideNetwork")')
        self.assertIn("IGUI_LWT_View_no_pressure|1", hide.toolTip.description)
        self.assertIn("IGUI_LWT_View_unfiltered|1", hide.toolTip.description)
        self.assertIsNone(lua.eval('option("ContextMenu_LWT_ShowNetwork")'))
        lua.execute('local o = option("ContextMenu_LWT_HideNetwork") o.run(unpack(o.args))')
        self.assertFalse(lua.eval("SPR.highlighted"))
        self.assertFalse(lua.eval("INLET.highlighted"))

    def test_a_new_view_replaces_the_old_one_and_no_per_frame_event(self):
        lua = self.view()
        lua.execute("reply({ { x = 2, y = 0, z = 0 } }) reply({ { x = 3, y = 0, z = 0 } })")
        self.assertFalse(lua.eval("SPR.highlighted"))
        self.assertTrue(lua.eval("INLET.highlighted"))
        for name in ("OnTick", "OnPlayerUpdate", "OnRenderTick", "OnPostRender", "OnPreUIDraw"):
            self.assertEqual(lua.eval("#Events.%s.handlers" % name), 0, name)


class Texts(unittest.TestCase):
    def test_translations(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            menu, ui = load("ContextMenu.json"), load("IG_UI.json")
            for key in ("ContextMenu_LWT_ShowNetwork", "ContextMenu_LWT_HideNetwork"):
                self.assertIn(key, menu, lang)
            for key in ("IGUI_LWT_View_served", "IGUI_LWT_View_no_pressure", "IGUI_LWT_View_unfiltered",
                        "IGUI_LWT_View_other", "IGUI_LWT_View_Title"):
                self.assertIn(key, ui, lang)


if __name__ == "__main__":
    unittest.main()
