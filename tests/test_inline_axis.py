"""ADR-008 D08 (G06): the flow meter and the inline valve keep the two sides of the axis they show (east-west or
north-south, chosen at placement with the furniture cursor). A pipe set down on one of their flanks is placed, but
not linked: no network link, no arm drawn towards the part, and the part keeps its straight tile. The axis is the
facing recorded on the part when it is set down (part definition field `sidesByFacing`), kept in the registry, so a
rebuild gives the same graph; a valve opened or closed keeps it."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua

METER = "shared/LiveWater/Parts/LWT_PartFlowMeter.lua"
VALVE = "shared/LiveWater/Parts/LWT_PartValve.lua"
TILE = "batman_livewater_01_"
METER_EW, METER_NS = TILE + "20", TILE + "21"
VALVE_EW, VALVE_NS, VALVE_EW_CLOSED = TILE + "16", TILE + "17", TILE + "18"


def world():
    lua = services(new_lua, METER, VALVE)
    lua.execute('PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function(m) table.insert(LOGS, m) end)'
                ' PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })'
                ' function set(x, y, sprite) WORLD:createPart(x, y, 0, sprite) return PLACEMENT:added(sprite, x, y, 0) end')
    return lua


def linked(lua, a, b):
    na = lua.eval("NET:networkAt(%d, %d, 0)" % a)
    return na is not None and na == lua.eval("NET:networkAt(%d, %d, 0)" % b)


class Flank(unittest.TestCase):
    def test_a_pipe_on_the_flank_of_an_east_west_meter_is_placed_but_not_linked(self):
        lua = world()
        lua.execute('set(0, 0, "%s") set(1, 0, "t_pipe_0") set(0, 1, "t_pipe_0")' % METER_EW)
        self.assertEqual(lua.eval("REG:at(0, 1, 0).type"), "Test:Pipe")
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 2)
        self.assertEqual(lua.eval("NET:mask(0, 1, 0)"), 0)
        self.assertEqual(lua.eval("WORLD:sprite(0, 1, 0)"), "t_pipe_0")
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), METER_EW)
        self.assertTrue(linked(lua, (0, 0), (1, 0)))
        self.assertFalse(linked(lua, (0, 0), (0, 1)))

    def test_a_pipe_on_the_flank_of_a_north_south_meter_is_placed_but_not_linked(self):
        lua = world()
        lua.execute('set(0, 0, "%s") set(0, -1, "t_pipe_0") set(1, 0, "t_pipe_0") set(-1, 0, "t_pipe_0")' % METER_NS)
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 1)
        self.assertEqual((lua.eval("NET:mask(1, 0, 0)"), lua.eval("NET:mask(-1, 0, 0)")), (0, 0))
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), "t_pipe_0")
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), METER_NS)

    def test_a_meter_set_down_by_a_flank_pipe_does_not_take_it(self):
        lua = world()
        lua.execute('set(0, 1, "t_pipe_0") set(0, 0, "%s")' % METER_EW)
        self.assertEqual((lua.eval("NET:mask(0, 0, 0)"), lua.eval("NET:mask(0, 1, 0)")), (0, 0))

    def test_a_valve_keeps_its_axis_open_and_closed(self):
        lua = world()
        lua.execute('set(0, 0, "%s") set(-1, 0, "t_pipe_0") set(0, 1, "t_pipe_0") VALVE = REG:at(0, 0, 0)' % VALVE_EW)
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 8)
        self.assertEqual(lua.eval("NET:mask(0, 1, 0)"), 0)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), VALVE_EW)
        lua.execute('LiveWater.Parts:call(VALVE, "open", false) PUB:present(VALVE)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), VALVE_EW_CLOSED)
        lua.execute('set(0, -1, "t_pipe_0")')
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 8)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), VALVE_EW_CLOSED)
        lua.execute('LiveWater.Parts:call(VALVE, "open", true) PUB:present(VALVE)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), VALVE_EW)
        self.assertEqual(lua.eval("NET:mask(0, 1, 0)"), 0)

    def test_a_valve_alone_on_a_flank_pipe_keeps_the_axis_it_shows(self):
        lua = world()
        lua.execute('set(0, 0, "%s") set(0, 1, "t_pipe_0") set(0, -1, "t_pipe_0")' % VALVE_EW)
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 0)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), VALVE_EW)


class Tee(unittest.TestCase):
    def test_a_meter_set_down_on_a_tee_links_only_along_its_axis(self):
        lua = world()
        lua.execute('set(-1, 0, "t_pipe_0") set(1, 0, "t_pipe_0") set(0, -1, "t_pipe_0") set(0, 0, "%s")' % METER_EW)
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 10)
        self.assertEqual(lua.eval("NET:mask(0, -1, 0)"), 0)
        self.assertTrue(linked(lua, (-1, 0), (1, 0)))
        self.assertFalse(linked(lua, (0, 0), (0, -1)))

    def test_a_north_south_meter_on_the_same_tee_takes_the_north_pipe_only(self):
        lua = world()
        lua.execute('set(-1, 0, "t_pipe_0") set(1, 0, "t_pipe_0") set(0, -1, "t_pipe_0") set(0, 0, "%s")' % METER_NS)
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 1)
        self.assertEqual((lua.eval("NET:mask(-1, 0, 0)"), lua.eval("NET:mask(1, 0, 0)")), (0, 0))


class Reload(unittest.TestCase):
    def test_a_rebuild_from_the_registry_gives_the_same_graph(self):
        lua = world()
        lua.execute('set(0, 0, "%s") set(1, 0, "t_pipe_0") set(0, 1, "t_pipe_0")'
                    ' set(5, 0, "%s") set(5, 1, "t_pipe_0") set(6, 0, "t_pipe_0")' % (METER_EW, VALVE_NS))
        squares = [(0, 0), (1, 0), (0, 1), (5, 0), (5, 1), (6, 0)]
        before = [lua.eval("NET:mask(%d, %d, 0)" % s) for s in squares]
        lua.execute("newServices(STORE) TOPO:rebuild()")
        self.assertEqual([lua.eval("NET:mask(%d, %d, 0)" % s) for s in squares], before)
        self.assertEqual(before, [2, 8, 0, 4, 1, 0])


class Definition(unittest.TestCase):
    def test_sides_by_facing_is_described_and_checked(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", METER, VALVE)
        for part in ("LiveWater:FlowMeter", "LiveWater:Valve"):
            d = lua.eval('LiveWater.API.part("%s")' % part)
            self.assertEqual((d.sidesByFacing[1], d.sidesByFacing[2]), (5, 10), part)
        for bad in ('{ [5] = 10 }', '{ [1] = 16 }', '"x"'):
            res = lua.eval('{ LiveWater.Parts:register("T:A%d", { variants = { a = { "z%d" } }, sidesByFacing = %s,'
                           ' capabilities = { conduit = true } }) }' % (len(bad), len(bad), bad))
            self.assertEqual((res[1], res[2]), (False, "invalid_sides_by_facing"), bad)

    def test_a_part_without_a_recorded_facing_offers_its_sides(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", METER)
        self.assertEqual(lua.eval('LiveWater.Parts:sidesOf({ type = "LiveWater:FlowMeter" })'), 15)
        self.assertEqual(lua.eval('LiveWater.Parts:sidesOf({ type = "LiveWater:FlowMeter", facing = 2 })'), 10)


if __name__ == "__main__":
    unittest.main()
