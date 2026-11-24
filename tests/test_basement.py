"""E19, ADR-026: the fixtures of the levels below ground that stand under the footprint of the
building an inlet touches are served, whether the basement belongs to the building or not; the fixtures of a basement
outside the footprint are not. ADR-026: a base the players built serves its two basement levels under its own circle.
Washing machines carry the waterPiped flag in 42.22, so they are fixtures like sinks."""
import unittest

from lwt_harness import new_lua

API = "shared/LiveWater/LWT_API.lua"

PROBE = r"""
HOUSE = { x1 = 0, y1 = 10, x2 = 9, y2 = 19, minLevel = 0, maxLevel = 1 }
function HOUSE:contains(x, y, z)
    return x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2 and z >= self.minLevel and z <= self.maxLevel
end
PROBE = { building = function(_, x, y, z) if HOUSE:contains(x, y + 1, z) then return HOUSE end end }
function area(x, y, z) return require("LiveWater/LWT_InletArea").of(PROBE, x, y, z, { building = 20, base = 12 }) end
-- A base the players built: the probe finds no map building (ADR-001 L11).
NOBUILDING = { building = function() end }
function base(x, y, z) return require("LiveWater/LWT_InletArea").of(NOBUILDING, x, y, z, { building = 20, base = 12 }) end
"""


class Basements(unittest.TestCase):
    def bench(self):
        lua = new_lua(API)
        lua.execute(PROBE)
        return lua

    def test_a_basement_under_the_footprint_is_served_even_outside_the_building(self):
        lua = self.bench()
        self.assertTrue(lua.eval("area(5, 9, 0):contains(3, 14, -1)"))
        self.assertTrue(lua.eval("area(5, 9, 0):contains(3, 14, -2)"))

    def test_a_basement_outside_the_footprint_is_not(self):
        lua = self.bench()
        self.assertFalse(lua.eval("area(5, 9, 0):contains(12, 14, -1)"))

    def test_the_basement_levels_are_scanned(self):
        lua = self.bench()
        self.assertLessEqual(lua.eval("area(5, 9, 0).minZ"), -2)

    def test_a_basement_of_the_building_itself_is_served(self):
        lua = self.bench()
        lua.execute("HOUSE.minLevel = -1")
        self.assertTrue(lua.eval("area(5, 9, 0):contains(3, 14, -1)"))


class PlayerBaseBasements(unittest.TestCase):
    """ADR-026 D01: outside a map building, the inlet serves its two basement levels too."""

    def bench(self):
        lua = new_lua(API)
        lua.execute(PROBE)
        return lua

    def test_the_basement_under_a_player_base_is_served(self):
        lua = self.bench()
        self.assertEqual(lua.eval("base(5, 9, 0).mode"), "base")
        self.assertTrue(lua.eval("base(5, 9, 0):contains(3, 14, -1)"))
        self.assertTrue(lua.eval("base(5, 9, 0):contains(3, 14, -2)"))

    def test_the_third_basement_level_is_out_of_the_area(self):
        # ADR-026 D02: the depth is InletArea.BASEMENT_LEVELS, one owner
        lua = self.bench()
        self.assertEqual(lua.eval("require('LiveWater/LWT_InletArea').BASEMENT_LEVELS"), 2)
        self.assertFalse(lua.eval("base(5, 9, 0):contains(3, 14, -3)"))

    def test_the_horizontal_range_still_holds_below_ground(self):
        lua = self.bench()
        self.assertTrue(lua.eval("base(5, 9, 0):contains(5, 20, -1)"))
        self.assertFalse(lua.eval("base(5, 9, 0):contains(5, 22, -1)"))


if __name__ == "__main__":
    unittest.main()
