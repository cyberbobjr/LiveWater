"""ADR-024: a fixture on a roof and "Unplumb". The area of an inlet on a map building also holds the squares above a
room of that building (its roof, storeys the players built on top, D03); the game's Plumb option is offered by
LiveWater on a roof only (a square outside any room whose square below is in a room) when a tank stands above the
fixture (D01, D02); the command "unplumb" puts a plumbed fixture back to "set down, to plumb", checked on the
authority (D04); a fixture taken from a roof or set down elsewhere on it loses and gets its relay (D06)."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
from test_inlet import TILE, bench

API = "shared/LiveWater/LWT_API.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
LANGS = ("CN", "DE", "EN", "ES", "FR", "JP", "KO", "PT", "PTBR", "RU", "TR")


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class RoofArea(unittest.TestCase):
    """The bench house: x 0..9, y 10..19, rooms on levels 0..4; the inlet at (5, 9, 0), range 20."""

    def area(self, lua):
        lua.execute("A = require('LiveWater/LWT_InletArea').of(PLUMB, 5, 9, 0, { building = 20, base = 12 })")

    def test_the_roof_of_the_building_is_in_the_area(self):
        lua = bench()
        self.area(lua)
        self.assertTrue(lua.eval("A:contains(2, 18, 5)"))

    def test_storeys_built_above_the_building_are_in_the_area(self):
        lua = bench()
        self.area(lua)
        self.assertTrue(lua.eval("A:contains(2, 18, 9)"))
        self.assertTrue(lua.eval("A:contains(2, 18, 31)"))

    def test_a_square_beside_the_building_is_not_its_roof(self):
        lua = bench()
        self.area(lua)
        self.assertFalse(lua.eval("A:contains(12, 18, 5)"))
        self.assertFalse(lua.eval("A:contains(12, 18, 0)"))

    def test_the_roof_of_a_lower_wing_is_in_the_area(self):
        # a hole in the upper floors: the square above the last room of that column is a roof
        lua = bench()
        lua.execute('HOUSE.holes = { ["3,12,2"] = true, ["3,12,3"] = true, ["3,12,4"] = true }')
        self.area(lua)
        self.assertTrue(lua.eval("A:contains(3, 12, 2)"))

    def test_the_range_still_limits_the_roof(self):
        lua = bench()
        lua.execute("PLUMB:addBuilding({ x1 = 100, y1 = 100, x2 = 160, y2 = 110, minLevel = 0, maxLevel = 0 })")
        lua.execute("A = require('LiveWater/LWT_InletArea').of(PLUMB, 99, 105, 0, { building = 10, base = 12 })")
        self.assertTrue(lua.eval("A:contains(105, 105, 1)"))
        self.assertFalse(lua.eval("A:contains(130, 105, 1)"))

    def test_a_fixture_on_the_roof_gets_its_relay(self):
        lua = bench()
        lua.execute("PLUMB:addFixture(4, 15, 5)")
        lua.execute('place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()' % TILE)
        self.assertEqual(lua.eval("relayAt(4, 15, 6).owner"), "5,9,0")


class RoofFixtureMoved(unittest.TestCase):
    def test_a_fixture_taken_from_the_roof_loses_its_relay_and_gets_one_where_it_is_set_down(self):
        # D06: nothing new, the survey after a fixture is taken or set down (LWT_Relays.touched)
        lua = bench()
        lua.execute("PLUMB:addFixture(4, 15, 5)")
        lua.execute('place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()' % TILE)
        self.assertIsNotNone(lua.eval("relayAt(4, 15, 6)"))
        lua.execute("table.remove(PLUMB.list) RELAYS:touched(4, 15) CLOCK:tick()")
        self.assertIsNone(lua.eval("relayAt(4, 15, 6)"))
        lua.execute("PLUMB:addFixture(8, 12, 5) RELAYS:touched(8, 12) CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(8, 12, 6).owner"), "5,9,0")


class PlumbRule(unittest.TestCase):
    def setUp(self):
        self.lua = new_lua(API)
        self.lua.execute("R = require('LiveWater/LWT_Plumbing')")

    def offer(self, info):
        return self.lua.eval("R.plumbOffer(%s)" % info)

    def test_plumb_is_offered_on_a_roof_with_a_tank_above(self):
        self.assertTrue(self.offer("{ plumbed = false, source = true, room = false, roomBelow = true }"))

    def test_not_in_a_room_where_the_game_offers_it(self):
        self.assertFalse(self.offer("{ plumbed = false, source = true, room = true, roomBelow = true }"))

    def test_not_in_the_garden(self):
        self.assertFalse(self.offer("{ plumbed = false, source = true, room = false, roomBelow = false }"))

    def test_not_without_a_tank_above(self):
        self.assertFalse(self.offer("{ plumbed = false, source = false, room = false, roomBelow = true }"))

    def test_not_for_a_plumbed_fixture_or_no_fixture(self):
        self.assertFalse(self.offer("{ plumbed = true, source = true, room = false, roomBelow = true }"))
        self.assertFalse(self.offer("nil"))

    def test_unplumb_is_for_a_plumbed_fixture(self):
        self.assertIsNone(self.lua.eval("R.unplumbRefusal({ plumbed = true })"))
        self.assertEqual(self.lua.eval("R.unplumbRefusal({ plumbed = false })"), "not_plumbed")
        self.assertEqual(self.lua.eval("R.unplumbRefusal(nil)"), "not_plumbed")


UNPLUMB = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end
FIX = { fixtures = {}, unplumbed = {} }
function FIX:plumbInfo(x, y, z) return self.fixtures[k(x, y, z)] end
function FIX:unplumb(x, y, z)
    self.fixtures[k(x, y, z)].plumbed = false
    table.insert(self.unplumbed, k(x, y, z))
    return true
end
CMDS = require("LiveWater/LWT_Commands").new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS,
    plumbing = FIX })
CMDS:register("unplumb", require("LiveWater/Commands/LWT_CmdUnplumb"))
P = newPlayer(1, 1, 0, nil, { ["base:pipewrench"] = true })
function cmd(x, y, z) return CMDS:dispatch(P, "unplumb", { x = x, y = y, z = z or 0 }) end
FIX.fixtures["2,2,0"] = { plumbed = true }
"""


class UnplumbCommand(unittest.TestCase):
    def bench(self):
        lua = services(new_lua)
        lua.execute(UNPLUMB)
        return lua

    def test_a_plumbed_fixture_goes_back_to_set_down(self):
        lua = self.bench()
        self.assertEqual(call(lua, "cmd(2, 2)"), (True, None))
        self.assertEqual(lua.eval("FIX.unplumbed[1]"), "2,2,0")

    def test_every_condition_is_checked_on_the_server(self):
        lua = self.bench()
        self.assertEqual(call(lua, "CMDS:dispatch(P, 'unplumb', { x = 'a', y = 2, z = 0 })"), (False, "invalid"))
        self.assertEqual(call(lua, "cmd(9, 9)"), (False, "not_plumbed"))
        lua.execute("P.x = 20")
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "too_far"))
        lua.execute("P.x = 1 P.tools = {}")
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "need_tool"))
        self.assertIsNone(lua.eval("FIX.unplumbed[1]"))

    def test_a_second_unplumb_is_refused(self):
        lua = self.bench()
        lua.execute("cmd(2, 2)")
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "not_plumbed"))

    def test_protocol_reason_and_translations(self):
        lua = new_lua(API)
        self.assertEqual(lua.eval("require('LiveWater/LWT_Protocol').UNPLUMB"), "unplumb")
        self.assertEqual(lua.eval("require('LiveWater/LWT_Reasons').key('not_plumbed')"), "IGUI_LWT_NoPlumbing")
        for lang in LANGS:
            found = {}
            for name in ("IG_UI.json", "ContextMenu.json"):
                with open(os.path.join(MEDIA, "lua", "shared", "Translate", lang, name), encoding="utf-8") as f:
                    found.update(json.load(f))
            for key in ("ContextMenu_LWT_Unplumb", "IGUI_LWT_NoPlumbing"):
                self.assertIn(key, found, lang)
            self.assertIn("%1", found["ContextMenu_LWT_Unplumb"], lang)


if __name__ == "__main__":
    unittest.main()
