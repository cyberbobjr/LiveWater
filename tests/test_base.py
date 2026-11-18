"""E26: player base, diagnostic, pickup (ADR-001 D28, L09, L11, L12): outside a map building the inlet serves the plumbed
fixtures within a range (12 by default, sandbox) up to 3 floors above; a fixture without water says why in one
translated line; a barrel set down again does not stay connected to its old house."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
from test_barrels import BARRELS
from test_inlet import BENCH, INLET, POND, TILE

API = "shared/LiveWater/LWT_API.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")

DIAG = r"""
DIAGNOSTICS = require("LiveWater/LWT_Diagnostics").new({ relays = RELAYS, barrels = BARRELS,
    pumped = function(part) return PUMPED[part.x .. "," .. part.y .. "," .. part.z] == true end })
CLOCK.chores = { RELAYS, BARRELS, DIAGNOSTICS }
"""


def bench():
    lua = services(new_lua, INLET, POND)
    lua.execute(BENCH)
    lua.execute(BARRELS)
    lua.execute(DIAG)
    return lua


class BaseMode(unittest.TestCase):
    def area(self, lua, x, y, z=0):
        lua.execute("A = require('LiveWater/LWT_InletArea').of(PLUMB, %d, %d, %d, RELAYS:ranges())" % (x, y, z))

    def test_away_from_a_map_building_the_inlet_serves_a_range(self):
        lua = bench()
        self.area(lua, 100, 100)
        self.assertEqual(lua.eval("A.mode"), "base")
        self.assertTrue(lua.eval("A:contains(110, 105, 0)"))
        self.assertFalse(lua.eval("A:contains(110, 110, 0)"))
        self.assertTrue(lua.eval("A:contains(101, 101, 3)"))
        self.assertFalse(lua.eval("A:contains(101, 101, 4)"))
        self.assertTrue(lua.eval("A:reaches(101, 101, 4)"))

    def test_the_range_is_a_sandbox_option(self):
        lua = bench()
        lua.execute("SETTINGS.BaseRange = 20")
        self.area(lua, 100, 100)
        self.assertTrue(lua.eval("A:contains(115, 110, 0)"))

    def test_relays_go_above_the_base_fixtures_in_range(self):
        lua = bench()
        lua.execute('PLUMB:addFixture(105, 105, 0) PLUMB:addFixture(130, 100, 0)'
                    ' place("LiveWater:HouseInlet", 100, 100, "%s40") CLOCK:tick()' % TILE)
        self.assertIsNotNone(lua.eval("relayAt(105, 105, 1)"))
        self.assertIsNone(lua.eval("relayAt(130, 100, 1)"))

    def test_the_original_fixtures_of_a_map_house_in_range_are_left_alone(self):
        # A map house east of the base, its own fixtures in range: only the fixture the players set down in the base
        # gets a relay (the house's sinks would draw invisible water after the city water shut-off).
        lua = bench()
        lua.execute('PLUMB:addBuilding({ x1 = 104, y1 = 98, x2 = 110, y2 = 106, minLevel = 0, maxLevel = 1 })'
                    ' PLUMB:addFixture(106, 102, 0) PLUMB:addFixture(97, 100, 0)'
                    ' place("LiveWater:HouseInlet", 100, 100, "%s40") CLOCK:tick()' % TILE)
        self.assertIsNotNone(lua.eval("relayAt(97, 100, 1)"))
        self.assertIsNone(lua.eval("relayAt(106, 102, 1)"))

    def test_a_map_house_fixture_already_fed_by_this_base_keeps_its_relay(self):
        lua = bench()
        lua.execute('PLUMB:addBuilding({ x1 = 104, y1 = 98, x2 = 110, y2 = 106, minLevel = 0, maxLevel = 1 })'
                    ' PLUMB:addFixture(106, 102, 0)'
                    ' PLUMB.relays["106,102,1"] = { owner = "100,100,0", amount = 0, capacity = 25 }'
                    ' STORE.relays["100,100,0"] = { ["106,102,1"] = { x = 106, y = 102, z = 1 } }'
                    ' place("LiveWater:HouseInlet", 100, 100, "%s40") CLOCK:tick()' % TILE)
        self.assertEqual(lua.eval("relayAt(106, 102, 1).owner"), "100,100,0")

    def test_sandbox_option_and_translations(self):
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("option LiveWater.BaseRange", text)
        self.assertIn("default = 12", text.split("option LiveWater.BaseRange")[1].split("}")[0])


class Diagnosis(unittest.TestCase):
    def setUp(self):
        self.lua = new_lua(API)
        self.lua.execute("D = require('LiveWater/LWT_Diagnosis')")

    def inlet(self, state, short, barrels, pumped):
        return self.lua.eval("D.inlet(%s, %s, %s, %s)" % (
            json.dumps(state) if state else "nil", json.dumps(short) if short else "nil",
            "true" if barrels else "false", "true" if pumped else "false"))

    def test_the_inlet_reason(self):
        self.assertEqual(self.inlet("unfiltered", None, False, True), "unfiltered")
        self.assertEqual(self.inlet("no_pressure", "gravity", True, True), "no_pressure")
        self.assertEqual(self.inlet("served", "gravity", True, False), "gravity")
        self.assertEqual(self.inlet("served", None, False, False), "no_supply")
        self.assertEqual(self.inlet(None, "empty", True, False), "empty")
        self.assertIsNone(self.inlet("served", None, False, True))

    def fixture(self, info):
        return self.lua.eval("D.fixture(%s)" % info)

    def test_the_fixture_line(self):
        self.assertEqual(self.fixture("{ plumbed = false, source = 'ours' }"), "IGUI_LWT_Why_NotPlumbed")
        self.assertEqual(self.fixture("{ plumbed = false }"), "IGUI_LWT_Why_NoInlet")
        self.assertEqual(self.fixture("{ plumbed = true }"), "IGUI_LWT_Why_NoInlet")
        self.assertEqual(self.fixture("{ plumbed = true, source = 'other' }"), "IGUI_LWT_Why_Other")
        self.assertEqual(self.fixture("{ plumbed = true, source = 'ours', why = 'gravity' }"), "IGUI_LWT_Why_gravity")
        self.assertEqual(self.fixture("{ plumbed = true, source = 'ours' }"), "IGUI_LWT_Why_Waiting")

    def test_every_line_is_translated(self):
        keys = ["IGUI_LWT_Why_" + k for k in ("NotPlumbed", "NoInlet", "Other", "Waiting", "unfiltered", "no_pressure",
                                               "no_water", "closed", "gravity", "empty", "no_supply")]
        keys += ["ContextMenu_LWT_NoWater"]
        for lang in ("EN", "FR"):
            found = {}
            for name in ("IG_UI.json", "ContextMenu.json"):
                with open(os.path.join(MEDIA, "lua", "shared", "Translate", lang, name), encoding="utf-8") as f:
                    found.update(json.load(f))
            for k in keys:
                self.assertIn(k, found, lang)


class Marks(unittest.TestCase):
    def test_the_relays_carry_the_reason_of_their_inlet(self):
        lua = bench()
        lua.execute('PLUMB:addFixture(2, 12, 0) PLUMB:addFixture(6, 16, 1) place("LiveWater:PondPump", 0, 9, "%s24")' % TILE)
        for x in range(1, 5):
            lua.execute('place("Test:Pipe", %d, 9)' % x)
        lua.execute('PUMPED["5,9,0"] = true CLOCK:tick() CLOCK:tick()')
        self.assertEqual(lua.eval("relayAt(2, 12, 1).why"), "unfiltered")

    def test_a_house_without_pump_nor_barrel_says_so(self):
        lua = bench()
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).why"), "no_supply")
        lua.execute("PLUMB:addBarrel(3, 13, 0, 100) BARRELS:connect(3, 13, 0) CLOCK:tick()")
        self.assertIsNone(lua.eval("relayAt(2, 12, 1).why"))
        self.assertEqual(lua.eval("relayAt(6, 16, 2).why"), "gravity")


class Pickup(unittest.TestCase):
    def test_a_barrel_set_down_again_forgets_its_old_house(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 0, { mark = { inlet = '50,50,0' } }) BARRELS:placed(3, 13, 0)")
        self.assertIsNone(lua.eval("barrelAt(3, 13, 0).mark"))

    def test_a_connected_barrel_keeps_its_mark(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 0) BARRELS:connect(3, 13, 0) BARRELS:placed(3, 13, 0)")
        self.assertEqual(lua.eval("barrelAt(3, 13, 0).mark.inlet"), "5,9,0")


if __name__ == "__main__":
    unittest.main()
