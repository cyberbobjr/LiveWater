"""Players combine barrels, fittings and pumps in unusual ways (ADR-001 D26, D28; ADR-005 D06, D07; ADR-011;
ADR-012): two fittings on one barrel, two pumps against one barrel, fuel and water on one network, barrels of another
fluid. Water is never created, a barrel never goes above its capacity nor below zero."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua
from test_drip import API, SETUP
from test_fitting import BENCH, FITTING, POND

# The containers port as the game behaves (LWT_GameContainers): add never beyond the free room, take never more than
# the amount, both answer the litres really moved.
FAITHFUL = r"""
function CONTAINERS:add(x, y, z, litres, quality)
    local c = CONT[x .. "," .. y]
    local n = math.min(litres, c.capacity - c.amount)
    if n <= 0 then return 0 end
    c.amount = c.amount + n
    if c.fluid == nil or c.fluid == "clean" or quality ~= "clean" then c.fluid = quality end
    return n
end
function CONTAINERS:take(x, y, z, litres)
    local c = CONT[x .. "," .. y]
    local n = math.min(litres, c.amount)
    c.amount = c.amount - n
    TAKEN = (TAKEN or 0) + n
    return n
end
function delivered()
    local total = 0
    for _, e in ipairs(emitted("waterDelivered")) do total = total + e[3] end
    return total
end
"""


def bench():
    lua = services(new_lua, POND, FITTING)
    lua.execute(BENCH)
    lua.execute(FAITHFUL)
    return lua


def domain(layout):
    lua = new_lua(API)
    lua.execute(SETUP)
    lua.execute(layout)
    lua.execute("step()")
    return lua


class TwoFittingsOnOneBarrel(unittest.TestCase):
    # Barrel at (2,-1) behind the fitting (2,0) of the bench; a second fitting at (1,-1) on the pipe (1,0) finds the
    # same barrel on its east side.
    SECOND = 'place("LiveWater:BarrelFitting", 1, -1, "batman_livewater_01_64")'

    def test_both_never_overflow_nor_take_more_than_the_free_room(self):
        lua = bench()
        lua.execute(self.SECOND)
        lua.execute('CONT["2,-1"] = { amount = 370, capacity = 400, fluid = "tainted" } tick()')
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 400)
        self.assertEqual(lua.eval("delivered()"), 30)


class TwoPumpsOnOneBarrel(unittest.TestCase):
    def test_two_networks_pumping_the_same_barrel_never_give_more_than_it_holds(self):
        lua = bench()
        lua.execute("""
        for _, k in ipairs({ "5,-2,0", "5,0,0" }) do WORLD.dry[k] = true WORLD.vessels[k] = true end
        place("LiveWater:PondPump", 5, -2, "batman_livewater_01_24") place("Test:Spr", 6, -2) NEED["6,-2"] = 100
        place("LiveWater:PondPump", 5, 0, "batman_livewater_01_24") place("Test:Spr", 6, 0) NEED["6,0"] = 100
        CONT["5,-1"] = { amount = 30, capacity = 400, fluid = "clean" }
        """)
        self.assertNotEqual(lua.eval("NET:networkAt(5, -2, 0)"), lua.eval("NET:networkAt(5, 0, 0)"))
        lua.execute("tick()")
        taken = lua.eval("TAKEN")
        self.assertGreater(taken, 0)
        self.assertLessEqual(taken, 30)
        self.assertAlmostEqual(lua.eval("delivered()"), taken)
        self.assertAlmostEqual(lua.eval('CONT["5,-1"].amount'), 30 - taken)


class FuelAndWaterBarrels(unittest.TestCase):
    """A third-party pump may give fuel (Test:FuelPump); LiveWater's own parts give water only."""

    def layout(self, pump):
        return domain("""
        put("%s", 0, 0) put("Test:Pipe", 1, 0) put("Test:Pipe", 2, 0)
        put("Test:Spr", 3, 0, 5) put("Test:Drip", 1, 1, 5) put("Test:Inlet", 2, 1, 5)
        put("Test:Fit", 0, 1, 5, { fitting = { found = true, fluid = "clean", amount = 10, free = 100 } })
        put("Test:Fit", 0, -1, 5, { fitting = { found = true, amount = 0, free = 100 } })
        """ % pump)

    def test_fuel_never_reaches_a_sprinkler_a_drip_line_or_a_house(self):
        lua = self.layout("Test:FuelPump")
        self.assertEqual([lua.eval("state(%d, %d)" % s) for s in ((3, 0), (1, 1), (2, 1))], ["wrong_fluid"] * 3)

    def test_fuel_never_goes_into_a_barrel_of_water_only_into_an_empty_one(self):
        lua = self.layout("Test:FuelPump")
        self.assertEqual((lua.eval("state(0, 1)"), lua.eval("state(0, -1)")), ("wrong_fluid", "served"))
        self.assertEqual(lua.eval('R.at["0,-1,0"].quality'), "fuel")

    def test_an_empty_barrel_on_a_water_network_gets_water(self):
        lua = self.layout("Test:CleanPump")
        self.assertEqual(lua.eval('R.at["0,-1,0"].quality'), "clean")


class BarrelOfAnotherFluid(unittest.TestCase):
    def test_a_barrel_of_another_fluid_is_never_drawn_the_pump_uses_its_pond(self):
        lua = domain('barrel(0, 0, "other", 100) put("Test:Spr", 0, 1, 10)')
        self.assertIsNone(lua.eval('R.drawn["0,0,0"]'))
        self.assertEqual((lua.eval("state(0, 1)"), lua.eval("R.quality")), ("served", "tainted"))

    def test_water_is_never_poured_on_top_of_another_fluid(self):
        lua = domain('put("Test:Pump", 0, 0) put("Test:Fit", 1, 0, 10, { fitting = { found = true,'
                     ' fluid = "other", amount = 10, free = 100 } })')
        self.assertEqual(lua.eval("state(1, 0)"), "wrong_fluid")


if __name__ == "__main__":
    unittest.main()
