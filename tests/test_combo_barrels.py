"""Players combine barrels and fittings in unusual ways (ADR-001 D26, D28; ADR-004 D04; ADR-005 D06, D07): two
fittings on one barrel, a barrel feeding another, fuel and water barrels on one network, barrels of another fluid,
barrels without pump, a house barrel that also has a fitting. Water is never created, a barrel never goes above its
capacity nor below zero."""
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
function mode(x, y, m) LiveWater.Parts:call(REG:at(x, y, 0), "setFittingMode", m) end
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

    def test_one_set_to_fill_and_one_to_pump_never_makes_water_over_many_steps(self):
        lua = bench()
        lua.execute(self.SECOND)
        lua.execute('mode(1, -1, "pump") CONT["2,-1"] = { amount = 380, capacity = 400, fluid = "clean" }')
        for _ in range(12):
            lua.execute("tick()")
            amount = lua.eval('CONT["2,-1"].amount')
            self.assertLessEqual(amount, 400)
            self.assertGreaterEqual(amount, 380 - 1e-9)

    def test_both_set_to_pump_never_give_more_than_the_barrel_holds(self):
        lua = bench()
        lua.execute(self.SECOND)
        lua.execute('mode(2, 0, "pump") mode(1, -1, "pump") CONT["2,-1"] = { amount = 30, capacity = 400, fluid = "clean" }'
                    ' place("Test:Spr", 1, 1) NEED["1,1"] = 100 tick()')
        self.assertLessEqual(lua.eval("delivered()"), 30 + 1e-9)
        self.assertAlmostEqual(lua.eval("TAKEN"), lua.eval("delivered()"))

    def test_two_networks_pumping_the_same_barrel_never_give_more_than_it_holds(self):
        lua = bench()
        lua.execute("""
        mode(2, 0, "pump") place("Test:Spr", 1, 1) NEED["1,1"] = 100
        place("LiveWater:PondPump", 4, -1) place("LiveWater:BarrelFitting", 3, -1, "batman_livewater_01_67")
        mode(3, -1, "pump") place("Test:Spr", 4, 0) NEED["4,0"] = 100
        CONT["2,-1"] = { amount = 30, capacity = 400, fluid = "clean" }
        """)
        self.assertNotEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(4, -1, 0)"))
        lua.execute("tick()")
        # every litre delivered was really taken from the barrel (the pumps draw the barrel, not their pond)
        taken = lua.eval("TAKEN")
        self.assertAlmostEqual(lua.eval("delivered()"), taken)
        self.assertAlmostEqual(lua.eval('CONT["2,-1"].amount'), 30 - taken)
        self.assertGreater(taken, 0)

    def test_both_set_to_fill_never_overflow_nor_take_more_than_the_free_room(self):
        lua = bench()
        lua.execute(self.SECOND)
        lua.execute('CONT["2,-1"] = { amount = 370, capacity = 400, fluid = "tainted" } tick()')
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 400)
        self.assertEqual(lua.eval("delivered()"), 30)


class OneBarrelFeedsAnother(unittest.TestCase):
    # Barrel A (2,-1) behind the bench fitting set to Pump; barrel B (1,2) behind a fitting set to Fill at (1,1).
    LAYOUT = """
    mode(2, 0, "pump") CONT["2,-1"] = { amount = 30, capacity = 400, fluid = "clean" }
    place("LiveWater:BarrelFitting", 1, 1, "batman_livewater_01_66") CONT["1,2"] = { amount = 0, capacity = 400 }
    """

    def test_with_a_pump_water_moves_from_a_to_b_never_more_than_a_holds(self):
        lua = bench()
        lua.execute(self.LAYOUT + "tick()")
        self.assertEqual((lua.eval('CONT["2,-1"].amount'), lua.eval('CONT["1,2"].amount')), (0, 30))
        self.assertEqual(lua.eval('CONT["1,2"].fluid'), "tainted")
        lua.execute("tick()")
        self.assertEqual(lua.eval("TAKEN"), 30)

    def test_b_takes_at_most_the_fitting_rate(self):
        lua = bench()
        lua.execute(self.LAYOUT + 'CONT["2,-1"].amount = 300 tick()')
        self.assertEqual((lua.eval('CONT["2,-1"].amount'), lua.eval('CONT["1,2"].amount')), (250, 50))

    def test_without_a_pump_nothing_moves_from_a_to_b(self):
        lua = domain("""
        barrel(0, 0, "clean", 30) put("Test:Pipe", 1, 0)
        put("Test:Fit", 2, 0, 50, { fitting = { mode = "fill", found = true, amount = 0, free = 400 } })
        """)
        self.assertEqual(lua.eval("state(2, 0)"), "no_pressure")
        self.assertEqual(lua.eval('R.drawn["0,0,0"].litres'), 0)


class FuelAndWaterBarrels(unittest.TestCase):
    def layout(self, near, far):
        return domain("""
        put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Pipe", 2, 0)
        barrel(1, -1, "%s", 100) barrel(2, -1, "%s", 100)
        put("Test:Spr", 3, 0, 5) put("Test:Drip", 1, 1, 5) put("Test:Inlet", 2, 1, 5)
        put("Test:Fit", 0, 1, 5, { fitting = { mode = "fill", found = true, fluid = "clean", amount = 10, free = 100 } })
        put("Test:Fit", 0, -1, 5, { fitting = { mode = "fill", found = true, amount = 0, free = 100 } })
        """ % (near, far))

    def test_the_nearest_barrel_sets_the_fluid_of_the_network(self):
        lua = self.layout("fuel", "clean")
        self.assertEqual(lua.eval("R.quality"), "fuel")
        self.assertIsNone(lua.eval('R.drawn["2,-1,0"]'))
        lua = self.layout("clean", "fuel")
        self.assertEqual(lua.eval("R.quality"), "clean")
        self.assertIsNone(lua.eval('R.drawn["2,-1,0"]'))

    def test_fuel_never_reaches_a_sprinkler_a_drip_line_or_a_house(self):
        lua = self.layout("fuel", "clean")
        self.assertEqual([lua.eval("state(%d, %d)" % s) for s in ((3, 0), (1, 1), (2, 1))], ["wrong_fluid"] * 3)

    def test_fuel_never_goes_into_a_barrel_of_water_only_into_an_empty_one(self):
        lua = self.layout("fuel", "clean")
        self.assertEqual((lua.eval("state(0, 1)"), lua.eval("state(0, -1)")), ("wrong_fluid", "served"))
        self.assertEqual(lua.eval('R.at["0,-1,0"].quality'), "fuel")

    def test_an_empty_barrel_on_a_water_network_gets_water(self):
        lua = self.layout("clean", "fuel")
        self.assertEqual(lua.eval('R.at["0,-1,0"].quality'), "clean")


class BarrelOfAnotherFluid(unittest.TestCase):
    def test_a_barrel_of_another_fluid_is_never_drawn_the_pump_uses_its_pond(self):
        lua = domain('put("Test:Pump", 0, 0) barrel(1, 0, "other", 100) put("Test:Spr", 0, 1, 10)')
        self.assertIsNone(lua.eval('R.drawn["1,0,0"]'))
        self.assertEqual((lua.eval("state(0, 1)"), lua.eval("R.quality")), ("served", "tainted"))

    def test_water_is_never_poured_on_top_of_another_fluid(self):
        lua = domain('put("Test:Pump", 0, 0) put("Test:Fit", 1, 0, 10, { fitting = { mode = "fill", found = true,'
                     ' fluid = "other", amount = 10, free = 100 } })')
        self.assertEqual(lua.eval("state(1, 0)"), "wrong_fluid")


class BarrelsWithoutPump(unittest.TestCase):
    def test_only_the_drip_lines_are_served_by_gravity(self):
        lua = domain("""
        barrel(0, 0, "clean", 100) put("Test:Drip", 1, 0, 2) put("Test:Spr", 1, 1, 1) put("Test:Inlet", 1, -1, 1)
        put("Test:Drip", 2, 0, 3)
        """)
        self.assertEqual([lua.eval("state(%d, %d)" % s) for s in ((1, 0), (2, 0), (1, 1), (1, -1))],
                         ["served", "served", "no_pressure", "no_pressure"])

    def test_two_barrels_give_a_gravity_pressure_of_one_not_two(self):
        lua = domain('barrel(0, 0, "clean", 100) put("Test:Drip", 1, 0, 2) barrel(2, 0, "clean", 100)')
        self.assertEqual(lua.eval("R.pressure"), 1)

    def test_the_barrel_empties_by_what_the_drip_lines_take(self):
        lua = bench()
        lua.execute("""
        TOPO:remove(0, 0, 0) TOPO:remove(1, 0, 0) mode(2, 0, "pump")
        CONT["2,-1"] = { amount = 7, capacity = 400, fluid = "tainted" }
        LiveWater.API.registerPart("Test:Drip", { sprites = { [0] = "t_drip" },
            capabilities = { conduit = true, outlet = { type = "drip" } } })
        OUTLETS:register("drip", { need = function() return 3 end, deliver = function() end })
        place("Test:Drip", 2, 1)
        """)
        for amount in (4, 1, 0, 0):
            lua.execute("tick()")
            self.assertAlmostEqual(lua.eval('CONT["2,-1"].amount'), amount)


# A barrel connected to the house (ADR-001 L01, D28) that also has a fitting: the containers port of the fittings
# reads and writes the same barrel as the house reserve (PLUMB.barrels of test_barrels).
HOUSE_FITTING = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end
HOUSE_CONTAINERS = {}
function HOUSE_CONTAINERS:at(x, y, z)
    local b = PLUMB.barrels[k(x, y, z)]
    if not b then return nil end
    return { fluid = b.amount > 0 and (b.fluid or "clean") or nil, amount = b.amount, free = b.capacity - b.amount }
end
function HOUSE_CONTAINERS:add(x, y, z, litres, quality)
    local b = PLUMB.barrels[k(x, y, z)]
    local n = math.min(litres, b.capacity - b.amount)
    b.amount, b.fluid = b.amount + n, quality
    return n
end
function HOUSE_CONTAINERS:take(x, y, z, litres)
    local b = PLUMB.barrels[k(x, y, z)]
    local n = math.min(litres, b.amount)
    b.amount = b.amount - n
    return n
end
FITTINGS = require("LiveWater/LWT_Fittings").new({ catalog = LiveWater.Parts, registry = REG, world = WORLD,
    containers = HOUSE_CONTAINERS, shapes = LiveWater.Containers })
OUTLETS:register("barrelFill", FITTINGS)
LiveWater.Events.on("waterDrawn", function(part, litres) FITTINGS:drawn(part, litres) end)
CLOCK.chores = { RELAYS, BARRELS, FITTINGS }
-- pond pump (3,8), pipes down to a fitting (3,12) on the house barrel (3,13), a pipe to the inlet (5,9)
place("LiveWater:PondPump", 3, 8, "batman_livewater_01_24")
for y = 9, 11 do place("Test:Pipe", 3, y) end
place("Test:Pipe", 4, 9)
place("LiveWater:BarrelFitting", 3, 12, "batman_livewater_01_64")
PLUMB:addBarrel(3, 13, 0, 100) BARRELS:connect(3, 13, 0)
-- not lifted: the barrel alone serves the ground floor, the network (drawing the same barrel) the floor above
function relays()
    local total = 0
    for _, r in pairs(PLUMB.relays) do total = total + r.amount end
    return total
end
function drink() for _, r in pairs(PLUMB.relays) do DRUNK = (DRUNK or 0) + r.amount r.amount = 0 end end
"""


class HouseBarrelWithAFitting(unittest.TestCase):
    def bench(self, fitting_mode):
        from test_barrels import BARRELS
        from test_inlet import BENCH as INLET_BENCH, INLET
        lua = services(new_lua, INLET, POND, FITTING)
        lua.execute(INLET_BENCH)
        lua.execute(BARRELS)
        lua.execute(HOUSE_FITTING)
        lua.execute('LiveWater.Parts:call(REG:at(3, 12, 0), "setFittingMode", "%s")' % fitting_mode)
        return lua

    def test_set_to_pump_the_house_and_the_network_share_the_barrel_without_making_water(self):
        lua = self.bench("pump")
        self.assertEqual(lua.eval("NET:networkAt(3, 12, 0)"), lua.eval("NET:networkAt(5, 9, 0)"))
        for _ in range(6):
            lua.execute("CLOCK:tick()")
            barrel = lua.eval("barrelAt(3, 13, 0).amount")
            self.assertGreaterEqual(barrel, 0)
            self.assertAlmostEqual(barrel + lua.eval("relays()") + lua.eval("DRUNK or 0"), 100)
            lua.execute("drink()")
        self.assertGreater(lua.eval("DRUNK"), 50)

    def test_set_to_fill_the_network_tops_the_house_barrel_up_never_beyond_its_capacity(self):
        lua = self.bench("fill")
        lua.execute("barrelAt(3, 13, 0).amount = 390")
        for _ in range(4):
            lua.execute("CLOCK:tick()")
            self.assertLessEqual(lua.eval("barrelAt(3, 13, 0).amount"), 400)
            lua.execute("drink()")
        self.assertEqual(lua.eval("barrelAt(3, 13, 0).fluid"), "tainted")


if __name__ == "__main__":
    unittest.main()
