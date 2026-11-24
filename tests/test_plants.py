"""ADR-027 D01: an outlet fills a plant up to its capacity, not up to its stage need.

The plant port is { alive, level, needed, max }: `needed` is the stage need of vanilla (waterNeeded) and `max`
its own capacity (waterNeededMax, nil when the crop declares none). One vanilla dose adds 10 points and the game
caps the level at 100.
"""
import unittest

from lwt_harness import new_lua

SETUP = r"""
PLANTS = require("LiveWater/LWT_Plants")
function doses(level, needed, max, alive)
    return PLANTS.dosesFor({ alive = alive ~= false, level = level, needed = needed, max = max })
end
"""


def plants():
    lua = new_lua("server/LiveWater/LWT_Plants.lua")
    lua.execute(SETUP)
    return lua


class Doses(unittest.TestCase):
    def test_the_stage_need_no_longer_stops_the_fill(self):
        # A plant at its stage need (70) still gets filled up to 100: 3 doses, not 0.
        self.assertEqual(plants().eval("doses(70, 70, nil)"), 3)

    def test_a_plant_under_its_capacity_gets_the_missing_doses(self):
        # 45 -> 100 misses 55 points: ceil(5.5) = 6 doses.
        self.assertEqual(plants().eval("doses(45, 70, nil)"), 6)

    def test_a_plant_at_95_gets_one_dose(self):
        self.assertEqual(plants().eval("doses(95, 70, nil)"), 1)

    def test_a_plant_at_its_capacity_gets_nothing(self):
        self.assertEqual(plants().eval("doses(100, 70, nil)"), 0)

    def test_a_declared_capacity_is_the_target(self):
        # waterNeededMax 85: 50 -> 85 misses 35 points, 4 doses.
        self.assertEqual(plants().eval("doses(50, 70, 85)"), 4)

    def test_a_declared_capacity_already_reached_gets_nothing(self):
        self.assertEqual(plants().eval("doses(85, 70, 85)"), 0)

    def test_a_capacity_below_the_stage_need_is_raised_to_the_need(self):
        # Contradictory modded data: the plant still gets what it needs to grow (70).
        self.assertEqual(plants().eval("doses(60, 70, 60)"), 1)

    def test_a_capacity_above_100_is_capped(self):
        # The game caps waterLvl at 100; 0 -> 100 is 10 doses.
        self.assertEqual(plants().eval("doses(0, 70, 120)"), 10)

    def test_a_zero_capacity_means_no_declared_cap(self):
        self.assertEqual(plants().eval("doses(0, 70, 0)"), 10)

    def test_a_need_of_zero_still_fills_to_the_capacity(self):
        self.assertEqual(plants().eval("doses(0, 0, nil)"), 10)

    def test_a_dead_plant_gets_nothing(self):
        self.assertEqual(plants().eval("doses(0, 70, nil, false)"), 0)

    def test_no_plant_gets_nothing(self):
        self.assertEqual(plants().eval("PLANTS.dosesFor(nil)"), 0)


if __name__ == "__main__":
    unittest.main()
