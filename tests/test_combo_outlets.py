"""Players combine outlets in unusual ways (ADR-001 D02, D14, D17, D18, D19; ADR-004 D02-D04; ADR-005 D01, D04): more
outlets than the pump pressure, a sprinkler and a drip line on the same plant, two house inlets, cartridges worn or
taken out, valves between the pump and some outlets."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua
from test_combo_pumps import domain
from test_inlet import BENCH as INLET_BENCH, INLET, POND, TILE
from test_sprinkler import BENCH as SPRINKLER_BENCH, SPRINKLER

DRIP = "shared/LiveWater/Parts/LWT_PartDripLine.lua"


def states(lua, squares):
    return [lua.eval("state(%d, %d)" % s) for s in squares]


class BeyondThePumpPressure(unittest.TestCase):
    # Clean pump (0,0), pipes x = 1..10 on y = 0; outlets on alternate rows so they never touch one another.
    LAYOUT = """
    put("Test:CleanPump", 0, 0) for x = 1, 10 do put("Test:Pipe", x, 0) end
    put("Test:Spr", 1, 1, 1) put("Test:Drip", 2, -1, 1) put("Test:Spr", 3, 1, 1) put("Test:Inlet", 4, -1, 1)
    put("Test:Spr", 5, 1, 1) put("Test:Drip", 6, -1, 1) put("Test:Spr", 7, 1, 1) put("Test:Spr", 8, -1, 1)
    """

    def test_outlets_are_served_by_pipe_distance_until_the_pressure_runs_out(self):
        lua = domain(self.LAYOUT)
        lua.execute("step()")
        order = lua.eval("R.outlets")
        self.assertEqual([order[i].key for i in range(1, 9)],
                         ["1,1,0", "2,-1,0", "3,1,0", "4,-1,0", "5,1,0", "6,-1,0", "7,1,0", "8,-1,0"])
        self.assertEqual(states(lua, [(1, 1), (2, -1), (3, 1), (4, -1), (5, 1), (6, -1), (7, 1), (8, -1)]),
                         ["served"] * 6 + ["no_pressure"] * 2)

    def test_the_drip_lines_pay_their_pressure_once_wherever_they_are(self):
        lua = domain(self.LAYOUT)
        lua.execute('step()')
        # 1 + 1 (both drip lines) + 1 + 2 + 1 = 6: the second drip line rides on the pressure the first one paid
        self.assertEqual(lua.eval("state(6, -1)"), "served")

    def test_a_drip_line_after_a_starved_outlet_stays_dry(self):
        # ADR-006 D04: the pressure fell at the end of the circuit, even if another drip line already paid the cost
        lua = domain(self.LAYOUT + 'put("Test:Drip", 9, 1, 1)')
        lua.execute("step()")
        self.assertEqual(lua.eval("state(9, 1)"), "no_pressure")


class SprinklerAndDripLineOnTheSamePlant(unittest.TestCase):
    """ADR-006 D01: each open outlet draws its own flow; the plant they share gets at most what it needs."""

    def test_each_outlet_draws_its_flow_and_the_plant_is_filled_by_the_first(self):
        lua = services(new_lua, POND, SPRINKLER, DRIP)
        lua.execute(SPRINKLER_BENCH)
        lua.execute("""
        OUTLETS:register("drip", require("LiveWater/LWT_Plants").new({ farming = FARM,
            area = require("LiveWater/LWT_DripArea").reach(LiveWater.Parts, NET) }))
        place("LiveWater:DripLine", 1, 1)
        LiveWater.Parts:call(SPR, "open", true)
        plant(2, 1, 0, 30)
        """)
        drawn = sum(e[3] for e in lua.eval("(function() EMITTED = {} CLOCK:tick() return emitted('waterDelivered') end)()").values())
        # ADR-027 D01: the sprinkler fills the plant to 100 (10 doses); the drip line then finds nothing to
        # water but still draws its flow. Both outlets draw, only the first delivers a dose.
        self.assertEqual(lua.eval("FARM.watered['2,1']"), 10)
        # sprinkler 10 L (SprinklerFlow) + one drip square 0.5 L (DripFlow), thirst or not
        self.assertAlmostEqual(drawn, 10.5)
        self.assertEqual((lua.eval("SPR.data.outlet.state"), lua.eval("REG:at(1, 1, 0).data.outlet.state")),
                         ("served", "served"))

    def test_two_sprinklers_on_one_plant_draw_twice_their_flow(self):
        lua = services(new_lua, POND, SPRINKLER)
        lua.execute(SPRINKLER_BENCH)
        lua.execute("""
        place("LiveWater:Sprinkler", 1, 1, "batman_livewater_01_48")
        LiveWater.Parts:call(SPR, "open", true) LiveWater.Parts:call(REG:at(1, 1, 0), "open", true)
        plant(2, 1, 0, 30)
        """)
        drawn = sum(e[3] for e in lua.eval("(function() EMITTED = {} CLOCK:tick() return emitted('waterDelivered') end)()").values())
        # ADR-027 D01: the first sprinkler fills the plant to 100 (10 doses), the second has nothing left.
        self.assertEqual(lua.eval("FARM.watered['2,1']"), 10)
        self.assertAlmostEqual(drawn, 20)


class TwoHouseInlets(unittest.TestCase):
    def bench(self):
        lua = services(new_lua, INLET, POND)
        lua.execute(INLET_BENCH)
        lua.execute("""
        WORLD.dry["0,9,0"] = true WORLD.near["0,9,0"] = { camping_01_16 = true }
        PLUMB:addFixture(2, 12, 0) PLUMB:addFixture(6, 16, 0)
        place("LiveWater:PondPump", 0, 9, "%s24")
        for x = 1, 4 do place("Test:Pipe", x, 9) end
        place("LiveWater:HouseInlet", 5, 9, "%s42")
        function relays()
            local total = 0
            for _, r in pairs(PLUMB.relays) do total = total + r.amount end
            return total
        end
        function delivered()
            local total = 0
            for _, e in ipairs(emitted("waterDelivered")) do total = total + e[3] end
            return total
        end
        """ % (TILE, TILE))
        return lua

    def test_two_inlets_on_one_house_fill_its_relays_once(self):
        lua = self.bench()
        lua.execute('place("Test:Pipe", -1, 9) place("LiveWater:HouseInlet", -1, 10, "%s42")' % TILE)
        lua.execute("EMITTED = {} CLOCK:tick()")
        self.assertEqual(lua.eval("relays()"), 50)
        self.assertEqual(lua.eval("delivered()"), 50)
        lua.execute("EMITTED = {} CLOCK:tick()")
        self.assertEqual((lua.eval("relays()"), lua.eval("delivered()")), (50, 0))

    def test_two_inlets_on_two_houses_both_get_water(self):
        lua = self.bench()
        lua.execute("""
        PLUMB:addBuilding({ x1 = 20, y1 = 10, x2 = 29, y2 = 19, minLevel = 0, maxLevel = 4 })
        PLUMB:addFixture(22, 12, 0)
        for x = 1, 19 do if not REG:at(x, 8, 0) then place("Test:Pipe", x, 8) end end
        place("Test:Pipe", 0, 8) place("Test:Pipe", 20, 8) place("LiveWater:HouseInlet", 20, 9, "%s42")
        CLOCK:tick() CLOCK:tick()
        """ % TILE)
        # one pump (50 L a step): the first house fills first, the second one the step after
        self.assertEqual(lua.eval("REG:at(20, 9, 0).data.outlet.state"), "served")
        self.assertEqual(lua.eval("relayAt(22, 12, 1).amount"), 25)
        self.assertEqual(lua.eval("relays()"), 75)


class InletCartridges(unittest.TestCase):
    def bench(self, well):
        lua = services(new_lua, INLET, POND)
        lua.execute(INLET_BENCH)
        if well:
            lua.execute('WORLD.dry["0,9,0"] = true WORLD.near["0,9,0"] = { camping_01_16 = true }')
        lua.execute('PLUMB:addFixture(2, 12, 0) place("LiveWater:PondPump", 0, 9, "%s24")'
                    ' for x = 1, 4 do place("Test:Pipe", x, 9) end place("LiveWater:HouseInlet", 5, 9, "%s42")'
                    ' INL = REG:at(5, 9, 0)' % (TILE, TILE))
        return lua

    def test_a_worn_cartridge_lets_no_pond_water_in(self):
        lua = self.bench(False)
        lua.execute('LiveWater.Parts:call(INL, "fit", 1) INL.data.filter.used = 500 CLOCK:tick()')
        self.assertEqual(lua.eval("INL.data.outlet.state"), "unfiltered")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).amount"), 0)

    def test_a_cartridge_taken_out_mid_network_stops_the_house_water_at_the_next_step(self):
        lua = self.bench(False)
        lua.execute('LiveWater.Parts:call(INL, "fit", 1) CLOCK:tick()')
        self.assertEqual(lua.eval("INL.data.outlet.state"), "served")
        lua.execute('relayAt(2, 12, 1).amount = 0 LiveWater.Parts:call(INL, "unfit") CLOCK:tick()')
        self.assertEqual(lua.eval("INL.data.outlet.state"), "unfiltered")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).amount"), 0)

    def test_clean_well_water_without_cartridge_is_served_and_the_light_is_green(self):
        lua = self.bench(True)
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("INL.data.outlet.state"), "served")
        self.assertEqual(lua.eval("WORLD:sprite(5, 9, 0)"), TILE + "42")


class ValvesBetweenPumpAndOutlets(unittest.TestCase):
    VALVE = "nil, { valve = { open = false } }"

    def test_a_closed_valve_before_the_house_keeps_the_sprinklers_upstream_served(self):
        lua = domain("""
        put("Test:CleanPump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Spr", 1, 1, 5) put("Test:Pipe", 2, 0)
        put("Test:Spr", 2, 1, 5) put("Test:Valve", 3, 0, %s) put("Test:Pipe", 4, 0) put("Test:Inlet", 5, 0, 10)
        """ % self.VALVE)
        lua.execute("step()")
        self.assertEqual(states(lua, [(1, 1), (2, 1), (5, 0)]), ["served", "served", "closed"])

    def test_a_closed_valve_on_a_drip_branch_dries_only_that_branch(self):
        lua = domain("""
        put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Valve", 1, 1, %s) put("Test:Drip", 1, 2, 5)
        put("Test:Drip", 1, 3, 5) put("Test:Drip", 2, 0, 5) put("Test:Drip", 3, 0, 5)
        """ % self.VALVE)
        lua.execute("step()")
        self.assertEqual(states(lua, [(1, 2), (1, 3), (2, 0), (3, 0)]), ["closed", "closed", "served", "served"])


if __name__ == "__main__":
    unittest.main()
