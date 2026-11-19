"""Players combine pumps in unusual ways (ADR-001 D02, D14, D15, D16): two pumps on one network, pumps that stop,
pumps with their four sides piped, two pumps behind a closed valve."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua
from test_drip import API, SETUP
from test_pump import BENCH as PUMP_BENCH, POND

# Domain bench of test_drip plus an inline valve.
VALVE = r"""
LiveWater.API.registerPart("Test:Valve", { sprites = { [0] = "t_valve" },
    capabilities = { conduit = { ports = 2 }, valve = true } })
function stepAt(x, y) R = FLOW:step(NET, NET:networkAt(x, y, 0), CTX) return R end
function through(x, y) return R.through[x .. "," .. y .. ",0"] or 0 end
"""


def domain(layout):
    lua = new_lua(API)
    lua.execute(SETUP)
    lua.execute(VALVE)
    lua.execute(layout)
    return lua


def states(lua, squares):
    return [lua.eval("state(%d, %d)" % s) for s in squares]


class TwoPumpsOnOneNetwork(unittest.TestCase):
    LINE = """
    put("Test:Pump", 0, 0) for x = 1, 8 do put("Test:Pipe", x, 0) end put("%s", 9, 0)
    for x = 1, 8 do put("Test:Spr", x, 1, 20) end
    """

    def test_two_pond_pumps_add_their_pressure_and_their_litres(self):
        lua = domain(self.LINE % "Test:Pump")
        lua.execute("step()")
        self.assertEqual((lua.eval("R.pressure"), lua.eval("R.water")), (12, 100))
        served = states(lua, [(x, 1) for x in range(1, 9)])
        self.assertEqual((served.count("served"), served.count("no_water")), (5, 3))
        self.assertEqual(lua.eval("R.served"), 100)

    def test_a_pond_pump_and_a_well_pump_give_tainted_water(self):
        lua = domain(self.LINE % "Test:CleanPump" + 'put("Test:Inlet", 0, 1, 10)')
        lua.execute("step()")
        self.assertEqual(lua.eval("R.quality"), "tainted")
        self.assertEqual(lua.eval("state(0, 1)"), "unfiltered")

    def test_each_pump_is_credited_its_share(self):
        lua = domain(self.LINE % "Test:Pump")
        lua.execute('NET:part(0, 0, 0).data = { pump = { efficiency = 50 } } step()')
        self.assertEqual(lua.eval("R.water"), 75)
        self.assertEqual((lua.eval("through(0, 0)"), lua.eval("through(9, 0)")), (25, 50))

    def test_one_pump_switched_off_broken_or_without_power_the_other_still_serves(self):
        for data in ("{ on = false }", "{ broken = true }", "{ efficiency = 0 }", "{ powered = false }"):
            lua = domain(self.LINE % "Test:Pump")
            lua.execute("NET:part(0, 0, 0).data = { pump = %s } step()" % data)
            self.assertEqual((lua.eval("R.pressure"), lua.eval("R.water")), (6, 50), data)
            self.assertEqual(lua.eval("through(9, 0)"), 50, data)
            self.assertEqual(lua.eval("R.served"), 50, data)


class PumpPickedUpMidNetwork(unittest.TestCase):
    def test_the_other_pump_keeps_serving_after_one_is_picked_up(self):
        lua = services(new_lua, POND)
        lua.execute(PUMP_BENCH)
        lua.execute("""
        place("LiveWater:PondPump", 0, 0) place("Test:Pipe", 1, 0) place("Test:Pipe", 2, 0)
        place("LiveWater:PondPump", 3, 0) place("Test:Spr", 1, 1) NEED["1,1"] = 80
        CLOCK:tick()
        """)
        self.assertEqual(lua.eval('REG:at(0, 0, 0).data.pump.litres + REG:at(3, 0, 0).data.pump.litres'), 80)
        lua.execute('TOPO:remove(0, 0, 0) EMITTED = {} CLOCK:tick()')
        delivered = lua.eval('emitted("waterDelivered")[1][3]')
        self.assertGreater(delivered, 49)
        self.assertAlmostEqual(lua.eval("REG:at(3, 0, 0).data.pump.litres"), delivered)


class PumpPorts(unittest.TestCase):
    def test_a_pump_takes_a_pipe_on_each_of_its_four_sides(self):
        lua = services(new_lua)
        lua.execute('place("Test:Pump", 0, 0)')
        for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.assertTrue(lua.eval('place("Test:Pipe", %d, %d)' % (x, y)), (x, y))
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 15)

    def test_a_pipe_beyond_the_pump_ports_is_refused_and_stays_apart(self):
        lua = services(new_lua, pump_ports=2)
        lua.execute('place("Test:Pump", 0, 0) place("Test:Pipe", 1, 0) place("Test:Pipe", -1, 0)')
        self.assertEqual(lua.eval('{ place("Test:Pipe", 0, 1) }')[2], "ports_full")
        self.assertIsNone(lua.eval("REG:at(0, 1, 0)"))

    def test_a_pipe_tee_next_to_the_pump_feeds_three_branches(self):
        lua = domain("""
        put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Pipe", 1, 1) put("Test:Pipe", 1, -1)
        put("Test:Pipe", 2, 0) put("Test:Spr", 1, 2, 5) put("Test:Spr", 1, -2, 5) put("Test:Spr", 3, 0, 5)
        """)
        lua.execute("step()")
        self.assertEqual(lua.eval("NET:mask(1, 0, 0)"), 15)
        self.assertEqual(states(lua, [(1, 2), (1, -2), (3, 0)]), ["served"] * 3)


class TwoPumpsBehindAClosedValve(unittest.TestCase):
    # pump A (0,0) - pipe - valve (2,0) - pipe - pump B (4,0); seven sprinklers on A's side, one on B's.
    LAYOUT = """
    put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Valve", 2, 0, nil, { valve = { open = false } })
    put("Test:Pipe", 3, 0) put("Test:Pump", 4, 0)
    put("Test:Pipe", 0, 1) for x = 0, 6 do put("Test:Pipe", x, 2) put("Test:Spr", x, 3, 10) end
    put("Test:Spr", 3, -1, 10)
    """

    def test_each_side_is_served_by_its_own_pump_only(self):
        lua = domain(self.LAYOUT)
        lua.execute("step()")
        a_side = states(lua, [(x, 3) for x in range(0, 7)])
        self.assertEqual(a_side.count("served"), 5)
        self.assertEqual(lua.eval("state(3, -1)"), "served")
        self.assertEqual(lua.eval("through(0, 0)"), 50)
        self.assertEqual(lua.eval("through(4, 0)"), 10)

    def test_a_side_without_pump_behind_the_closed_valve_gets_nothing(self):
        lua = domain("""
        put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Valve", 2, 0, nil, { valve = { open = false } })
        put("Test:Pipe", 3, 0) put("Test:Spr", 3, 1, 10) put("Test:Spr", 1, 1, 10)
        """)
        lua.execute("step()")
        self.assertEqual(states(lua, [(1, 1), (3, 1)]), ["served", "closed"])

    def test_opening_the_valve_merges_the_two_sides(self):
        lua = domain(self.LAYOUT)
        lua.execute("NET:part(2, 0, 0).data.valve.open = true step()")
        a_side = states(lua, [(x, 3) for x in range(0, 7)])
        self.assertEqual(lua.eval("R.pressure"), 12)
        self.assertEqual(a_side.count("served"), 7)
        self.assertEqual(lua.eval("state(3, -1)"), "served")


if __name__ == "__main__":
    unittest.main()
