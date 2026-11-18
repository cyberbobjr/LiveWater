"""E22 review, ADR-001 D04: every entry LiveWater keeps in the global ModData carries `v` (version of its schema) and
keeps the fields it does not know (data of a newer version) when it is written again."""
import unittest

from test_barrels import bench as barrels_bench
from test_inlet import TILE, bench as inlet_bench


class RelayRecords(unittest.TestCase):
    def test_a_relay_record_is_versioned_and_keeps_unknown_fields(self):
        lua = inlet_bench()
        lua.execute('PLUMB:addFixture(2, 12, 0) place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()' % TILE)
        self.assertEqual(lua.eval('STORE.relays["5,9,0"]["2,12,1"].v'), 1)
        lua.execute('STORE.relays["5,9,0"]["2,12,1"].later = "kept" RELAYS:refresh(REG:at(5, 9, 0), true)')
        self.assertEqual(lua.eval('STORE.relays["5,9,0"]["2,12,1"].later'), "kept")

    def test_an_orphan_relay_is_versioned(self):
        lua = inlet_bench()
        lua.execute('PLUMB:addFixture(2, 12, 0) place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()' % TILE)
        lua.execute('PLUMB.unloaded["2,12,1"] = true TOPO:remove(5, 9, 0)')
        self.assertEqual(lua.eval('STORE.orphans["2,12,1"].v'), 1)


class BarrelRecords(unittest.TestCase):
    def test_a_barrel_record_is_versioned(self):
        lua = barrels_bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 100) CLOCK:tick()")
        self.assertTrue(lua.eval("BARRELS:connect(3, 13, 0)"))
        self.assertEqual(lua.eval('STORE.barrels["5,9,0"]["3,13,0"].v'), 1)


class MirroredState(unittest.TestCase):
    def test_the_state_mirrored_on_a_part_is_versioned(self):
        # The mirror travels with the furniture item when a pump is picked up (wear, filter).
        lua = inlet_bench()
        lua.execute('WORLD.dry["0,9,0"] = true WORLD.near["0,9,0"] = { camping_01_16 = true } place("LiveWater:PondPump", 0, 9, "%s24") PUB:present(REG:at(0, 9, 0))' % TILE)
        self.assertEqual(lua.eval('WORLD.states["0,9,0"].v'), 1)


if __name__ == "__main__":
    unittest.main()
