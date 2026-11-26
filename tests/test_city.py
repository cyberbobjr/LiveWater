"""E27: connect a fixture to the city water (ADR-001 D27, D28, M01): on a water fixture a player set down inside a map
building, while the city water still runs, the authority restores the state of an original fixture (no ModData
canBeWaterPiped, no outside source: IsoObject.isWaterInfinite, Java 42.22) and sends it; every condition is checked
again on the server: a plumbable fixture, a map building, the player in reach, the city water running."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")

BENCH = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end
CITY = { runs = true, fixtures = {}, connected = {} }
function CITY:cityWaterRuns() return self.runs end
function CITY:cityFixture(x, y, z) return self.fixtures[k(x, y, z)] end
function CITY:connectCity(x, y, z) table.insert(self.connected, k(x, y, z)) return true end
CMDS = require("LiveWater/LWT_Commands").new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS,
    plumbing = CITY })
CMDS:register("cityWater", require("LiveWater/Commands/LWT_CmdCityWater"))
P = newPlayer(1, 1, 0)
function cmd(x, y, z) return CMDS:dispatch(P, "cityWater", { x = x, y = y, z = z or 0 }) end
-- A sink set down by a player in a room of a map building, not plumbed.
CITY.fixtures["2,2,0"] = { placed = true, plumbed = false, room = true, noWater = false }
"""


def bench():
    lua = services(new_lua)
    lua.execute(BENCH)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class CityWater(unittest.TestCase):
    def test_a_placed_fixture_in_a_map_building_joins_the_city_water(self):
        lua = bench()
        self.assertEqual(call(lua, "cmd(2, 2)"), (True, None))
        self.assertEqual(lua.eval("CITY.connected[1]"), "2,2,0")

    def test_a_fixture_plumbed_with_no_tank_above_joins_the_city_water(self):
        # The game's own "Plumb" is offered without a tank above before the shut-off; the fixture then stays dry.
        lua = bench()
        lua.execute('CITY.fixtures["2,2,0"] = { placed = false, plumbed = true, source = false, room = true }')
        self.assertEqual(call(lua, "cmd(2, 2)"), (True, None))
        self.assertEqual(lua.eval("CITY.connected[1]"), "2,2,0")

    def test_every_condition_is_checked_on_the_server(self):
        lua = bench()
        self.assertEqual(call(lua, "cmd(9, 9)"), (False, "not_fixture"))
        lua.execute('CITY.fixtures["2,2,0"].plumbed = true CITY.fixtures["2,2,0"].source = true')
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "not_fixture"))
        lua.execute('CITY.fixtures["2,2,0"].plumbed = false CITY.fixtures["2,2,0"].placed = false')
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "not_fixture"))
        lua.execute('CITY.fixtures["2,2,0"].placed = true P.x = 20')
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "too_far"))
        lua.execute('P.x = 1 CITY.fixtures["2,2,0"].room = false')
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "not_map_building"))
        lua.execute('CITY.fixtures["2,2,0"].room = true CITY.runs = false')
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "no_city_water"))
        lua.execute('CITY.runs = true CITY.fixtures["2,2,0"].noWater = true')
        self.assertEqual(call(lua, "cmd(2, 2)"), (False, "no_city_water"))
        self.assertIsNone(lua.eval("CITY.connected[1]"))

    def test_the_rule_shared_with_the_menu(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua")
        lua.execute("R = require('LiveWater/LWT_CityWater')")
        self.assertIsNone(lua.eval("R.refusal({ placed = true, plumbed = false, room = true }, true)"))
        self.assertEqual(lua.eval("R.refusal({ placed = true, plumbed = false, room = true }, false)"), "no_city_water")
        self.assertEqual(lua.eval("R.refusal(nil, true)"), "not_fixture")

    def test_translations_and_protocol(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua")
        self.assertEqual(lua.eval("require('LiveWater/LWT_Protocol').CITY_WATER"), "cityWater")
        for lang in ("EN", "FR"):
            found = {}
            for name in ("IG_UI.json", "ContextMenu.json"):
                with open(os.path.join(MEDIA, "lua", "shared", "Translate", lang, name), encoding="utf-8") as f:
                    found.update(json.load(f))
            for key in ("ContextMenu_LWT_CityWater", "IGUI_LWT_NotFixture", "IGUI_LWT_NotMapBuilding",
                        "IGUI_LWT_NoCityWater"):
                self.assertIn(key, found, lang)


if __name__ == "__main__":
    unittest.main()
