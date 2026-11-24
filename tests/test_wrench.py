"""The pipe wrench rule the client options and the authority share (ADR-024 D01, D04): the game
accepts a pipe wrench by type or by tag, in the inventory (bags included), as long as it is not
broken; an option LiveWater offers is therefore never refused as "need_tool", and a fixture left to
plumb says when the pipe wrench is missing or broken (the game's own message does not). Player report
of 2026-11-24: "the right click plumb option states I need a pipe wrench even when actively holding
it"."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua

API = "shared/LiveWater/LWT_API.lua"
WRENCH = "shared/LiveWater/LWT_Wrench.lua"
PLAYERS = "server/LiveWater/LWT_GamePlayers.lua"

BENCH = r"""
ItemTag = { PIPE_WRENCH = "PipeWrenchTag" }
function item(type, o)
    o = o or {}
    o.type = type
    o.broken = o.broken or false
    o.tags = o.tags or {}
    o.getType = function(self) return self.type end
    o.isBroken = function(self) return self.broken end
    o.hasTag = function(self, tag)
        for i = 1, #self.tags do if self.tags[i] == tag then return true end end
        return false
    end
    return o
end
-- Inventory double with the two scans the game offers (bags recurse there; the list is flat here).
function inventory(items)
    local inv = { items = items }
    function inv:getFirstTypeEvalRecurse(type, fn)
        for i = 1, #self.items do
            local it = self.items[i]
            if it:getType() == type and fn(it) then return it end
        end
        return nil
    end
    function inv:getFirstTagEvalRecurse(tag, fn)
        for i = 1, #self.items do
            local it = self.items[i]
            if it:hasTag(tag) and fn(it) then return it end
        end
        return nil
    end
    return inv
end
function playerWith(items)
    local inv = inventory(items)
    return { getInventory = function() return inv end }
end
W = require("LiveWater/LWT_Wrench")
"""


class WrenchRule(unittest.TestCase):
    def setUp(self):
        self.lua = new_lua(API, WRENCH)
        self.lua.execute(BENCH)

    def first(self, expr):
        return self.lua.eval("W.first(inventory(%s))" % expr)

    def test_the_game_pipe_wrench_by_type(self):
        self.assertIsNotNone(self.first('{ item("PipeWrench") }'))

    def test_a_pipe_wrench_by_tag_only(self):
        self.assertIsNotNone(self.first('{ item("PipeWrenchOfAnotherMod", { tags = { "PipeWrenchTag" } }) }'))

    def test_a_broken_pipe_wrench_does_not_count(self):
        self.assertIsNone(self.first('{ item("PipeWrench", { broken = true }) }'))
        self.assertIsNone(self.first('{ item("Modded", { tags = { "PipeWrenchTag" }, broken = true }) }'))

    def test_a_good_pipe_wrench_behind_a_broken_one_counts(self):
        self.lua.execute('BROKEN = item("PipeWrench", { broken = true }) GOOD = item("PipeWrench")')
        self.assertTrue(self.lua.eval("W.first(inventory({ BROKEN, GOOD })) == GOOD"))

    def test_a_plain_wrench_is_not_a_pipe_wrench(self):
        self.assertIsNone(self.first('{ item("Wrench") }'))

    def test_the_reason_the_player_may_not_plumb(self):
        self.assertIsNone(self.lua.eval('W.problem(playerWith({ item("PipeWrench") }))'))
        self.assertEqual(self.lua.eval('W.problem(playerWith({ item("PipeWrench", { broken = true }) }))'),
                         "wrench_broken")
        self.assertEqual(self.lua.eval('W.problem(playerWith({ item("Wrench") }))'), "no_wrench")
        self.assertIsNone(self.lua.eval("W.problem(nil)"))


class Authority(unittest.TestCase):
    """LWT_GamePlayers is the authority's port: it asks the same rule, so a pipe wrench the client
    menu accepts (by type, without the tag) is not refused with "need_tool"."""

    def setUp(self):
        self.lua = new_lua(API, WRENCH, PLAYERS)
        self.lua.execute(BENCH)
        self.lua.execute('PORT = require("LiveWater/LWT_GamePlayers").new()')

    def has(self, expr):
        return self.lua.eval("PORT:hasWrench(playerWith(%s))" % expr)

    def test_the_authority_accepts_a_pipe_wrench_by_type_or_tag(self):
        self.assertTrue(self.has('{ item("PipeWrench") }'))
        self.assertTrue(self.has('{ item("Modded", { tags = { "PipeWrenchTag" } }) }'))

    def test_the_authority_refuses_a_broken_or_absent_pipe_wrench(self):
        self.assertFalse(self.has('{ item("PipeWrench", { broken = true }) }'))
        self.assertFalse(self.has('{ item("Wrench") }'))
        self.assertFalse(self.has("{}"))


UNPLUMB = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end
FIX = { fixtures = {} }
function FIX:plumbInfo(x, y, z) return self.fixtures[k(x, y, z)] end
function FIX:unplumb(x, y, z) self.fixtures[k(x, y, z)].plumbed = false return true end
PORT = { asked = 0, wrench = true }
function PORT:position(p) return p.x, p.y, p.z end
function PORT:hasWrench(p) self.asked = self.asked + 1 return self.wrench end
function PORT:tell(p, key) p.told = key end
CMDS = require("LiveWater/LWT_Commands").new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD,
    players = PORT, plumbing = FIX })
CMDS:register("unplumb", require("LiveWater/Commands/LWT_CmdUnplumb"))
P = newPlayer(1, 1, 0)
FIX.fixtures["2,2,0"] = { plumbed = true }
function cmd() return CMDS:dispatch(P, "unplumb", { x = 2, y = 2, z = 0 }) end
"""


class UnplumbCommand(unittest.TestCase):
    def bench(self):
        lua = services(new_lua)
        lua.execute(UNPLUMB)
        return lua

    def test_the_command_asks_the_shared_wrench_rule(self):
        lua = self.bench()
        self.assertTrue(lua.eval("cmd()"))
        self.assertEqual(lua.eval("PORT.asked"), 1)

    def test_a_refused_wrench_is_told_with_the_tool_line(self):
        lua = self.bench()
        lua.execute("PORT.wrench = false")
        out = lua.eval("{ cmd() }")
        self.assertEqual((out[1], out[2]), (False, "need_tool"))
        self.assertEqual(lua.eval("P.told"), "IGUI_LWT_NeedTool")


MENUS = r"""
ItemTag = { PIPE_WRENCH = "PipeWrenchTag" }
function getText(key, a) if a ~= nil then return key .. "|" .. tostring(a) end return key end
function getItemName(t) return t end
function getTexture(t) return t end
ISWorldObjectContextMenu = { addToolTip = function() local t = {} function t:setName(n) self.name = n end return t end }
WM = require("LiveWater/LWT_WrenchMenu")
function dressed(wrench, items)
    local o = {}
    WM.dress(o, "Plumb Sink", wrench, playerWith(items))
    return o
end
"""


class WrenchMenu(unittest.TestCase):
    def setUp(self):
        self.lua = new_lua(API, WRENCH)
        self.lua.execute(BENCH)
        self.lua.execute('require("LiveWater/LWT_WrenchMenu")')
        self.lua.execute(MENUS)

    def test_without_a_pipe_wrench_the_option_keeps_the_game_line(self):
        self.lua.execute('O = dressed(nil, { item("Wrench") })')
        self.assertTrue(self.lua.eval("O.notAvailable"))
        self.assertEqual(self.lua.eval("O.toolTip.description"), "Tooltip_NeedWrench|Base.PipeWrench")

    def test_a_broken_pipe_wrench_is_named(self):
        self.lua.execute('O = dressed(nil, { item("PipeWrench", { broken = true }) })')
        self.assertTrue(self.lua.eval("O.notAvailable"))
        self.assertEqual(self.lua.eval("O.toolTip.description"), "IGUI_LWT_WrenchBroken")

    def test_with_a_pipe_wrench_the_option_stays_open(self):
        self.lua.execute('local w = item("PipeWrench") O = dressed(w, { w })')
        self.assertFalse(self.lua.eval("O.notAvailable == true"))
        self.assertIsNone(self.lua.eval("O.toolTip"))


if __name__ == "__main__":
    unittest.main()
