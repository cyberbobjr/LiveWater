"""Players build unusual shapes (ADR-001 D10, D12, D14; ADR-002 D01-D05; ADR-004 D01): pipe loops, networks without a
pump, walls and fences between parts, parts picked up and set down again in the middle of a network, a world saved and
loaded again."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua
from test_combo_pumps import domain
from test_filter import BENCH as FILTER_BENCH, INLET
from test_pump import BENCH as PUMP_BENCH, POND
from test_sprinkler import BENCH as SPRINKLER_BENCH, SPRINKLER

DRIP = "shared/LiveWater/Parts/LWT_PartDripLine.lua"
FITTING = "shared/LiveWater/Parts/LWT_PartBarrelFitting.lua"
TILE = "batman_livewater_01_"


def pumps():
    lua = services(new_lua, POND, DRIP)
    lua.execute(PUMP_BENCH)
    lua.execute("""
    PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function() end, WORLD)
    function delivered()
        EMITTED = {} CLOCK:tick()
        local total = 0
        for _, e in ipairs(emitted("waterDelivered")) do total = total + e[3] end
        return total
    end
    -- as the composition root wires it (LWT_Server)
    LiveWater.Events.on("networkChanged", function(id) CLOCK:settle(id) end)
    function outletState(x, y) return REG:at(x, y, 0).data.outlet and REG:at(x, y, 0).data.outlet.state end
    """)
    return lua


class Shapes(unittest.TestCase):
    def test_a_loop_of_pipes_with_the_pump_in_it_serves_each_outlet_once(self):
        lua = domain("""
        put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Pipe", 1, 1) put("Test:Pipe", 0, 1)
        put("Test:Pipe", -1, 1) put("Test:Pipe", -1, 0) put("Test:Spr", 2, 1, 5) put("Test:Spr", -2, 1, 5)
        """)
        lua.execute("step()")
        self.assertEqual((lua.eval("state(2, 1)"), lua.eval("state(-2, 1)")), ("served", "served"))
        self.assertEqual(lua.eval("R.served"), 10)
        self.assertEqual(lua.eval("#R.outlets"), 2)

    def test_pipes_and_outlets_without_any_pump_serve_nothing_and_raise_nothing(self):
        lua = domain('put("Test:Pipe", 0, 0) put("Test:Spr", 1, 0, 5) put("Test:Inlet", 0, 1, 5)')
        lua.execute("step()")
        self.assertEqual((lua.eval("R.served"), lua.eval("R.pressure")), (0, 0))

    def test_a_part_alone_serves_nothing(self):
        lua = domain('put("Test:Spr", 0, 0, 5)')
        lua.execute("step()")
        self.assertEqual(lua.eval("R.served"), 0)

    def test_drip_lines_linked_only_to_one_another_stay_dry(self):
        lua = domain('put("Test:Drip", 0, 0, 5) put("Test:Drip", 1, 0, 5) put("Test:Drip", 1, 1, 5)')
        lua.execute("step()")
        self.assertEqual((lua.eval("R.served"), lua.eval("NET:mask(1, 0, 0)")), (0, 12))

    def test_a_network_without_pump_is_left_asleep_by_the_clock(self):
        lua = pumps()
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Spr", 1, 0) NEED["1,0"] = 5')
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertEqual(lua.eval("#CLOCK:tick()"), 0)


class WallsAndFences(unittest.TestCase):
    def test_a_wall_between_the_pump_and_its_pipe_keeps_them_apart(self):
        lua = pumps()
        lua.execute('WORLD:setEdge(1, 0, 0, false, "wall") place("LiveWater:PondPump", 0, 0) place("Test:Pipe", 1, 0)'
                    ' place("Test:Spr", 2, 0) NEED["2,0"] = 5')
        self.assertNotEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(1, 0, 0)"))
        self.assertEqual(lua.eval("delivered()"), 0)

    def test_a_drip_line_crosses_a_fence_without_a_sleeve(self):
        lua = pumps()
        lua.execute('WORLD:setEdge(1, 0, 0, false, "fence") place("LiveWater:DripLine", 0, 0)'
                    ' place("LiveWater:DripLine", 1, 0)')
        self.assertEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(1, 0, 0)"))
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), TILE + str(160 + 8))

    def test_a_wall_built_later_cuts_the_far_side_at_the_next_step(self):
        lua = pumps()
        lua.execute('place("LiveWater:PondPump", 0, 0) place("Test:Pipe", 1, 0) place("Test:Pipe", 2, 0)'
                    ' place("Test:Spr", 3, 0) NEED["3,0"] = 5')
        self.assertEqual(lua.eval("delivered()"), 5)
        lua.execute('WORLD:setEdge(2, 0, 0, false, "wall") TOPO:refreshCuts(function() return true end)')
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertNotEqual(lua.eval("outletState(3, 0)"), "served")


    def test_a_wall_taken_away_next_to_a_full_valve_keeps_its_two_ports(self):
        # ADR-006 D05: the part placed last (the third pipe) stays apart, now and after a rebuild
        lua = services(new_lua, "shared/LiveWater/Parts/LWT_PartValve.lua")
        lua.execute("""
        place("Test:Pipe", 0, 0) place("LiveWater:Valve", 1, 0, "batman_livewater_01_16") place("Test:Pipe", 2, 0)
        WORLD:setEdge(1, 0, 0, true, "wall") place("Test:Pipe", 1, -1)
        WORLD:setEdge(1, 0, 0, true, nil) TOPO:relink(1, 0, 0)
        """)
        self.assertLessEqual(len(lua.eval("NET:linksOf(NET:part(1, 0, 0))")), 2)
        before = lua.eval("NET:mask(1, 0, 0)")
        lua.execute("newServices(STORE) TOPO:rebuild()")
        self.assertEqual(lua.eval("NET:mask(1, 0, 0)"), before)
        self.assertIsNotNone(lua.eval("NET:part(1, -1, 0)"))

    def test_the_part_kept_apart_links_again_once_the_full_valve_is_picked_up(self):
        lua = services(new_lua, "shared/LiveWater/Parts/LWT_PartValve.lua")
        lua.execute("""
        place("Test:Pipe", 0, 0) place("LiveWater:Valve", 1, 0, "batman_livewater_01_16") place("Test:Pipe", 2, 0)
        WORLD:setEdge(1, 0, 0, true, "wall") place("Test:Pipe", 1, -1)
        WORLD:setEdge(1, 0, 0, true, nil) TOPO:relink(1, 0, 0)
        TOPO:remove(1, 0, 0) place("Test:Pipe", 1, 0)
        """)
        self.assertEqual(lua.eval("NET:networkAt(1, -1, 0)"), lua.eval("NET:networkAt(1, 0, 0)"))

    def test_a_valve_placed_last_keeps_its_first_two_links(self):
        # the valve is the newer part of the link that appears: it keeps the two pipes it was set down with
        lua = services(new_lua, "shared/LiveWater/Parts/LWT_PartValve.lua")
        lua.execute("""
        place("Test:Pipe", 0, 0) place("Test:Pipe", 2, 0) WORLD:setEdge(1, 0, 0, true, "wall") place("Test:Pipe", 1, -1)
        place("LiveWater:Valve", 1, 0, "batman_livewater_01_16")
        WORLD:setEdge(1, 0, 0, true, nil) TOPO:relink(1, 0, 0)
        """)
        self.assertEqual(lua.eval("NET:mask(1, 0, 0)"), 2 + 8)
        self.assertNotEqual(lua.eval("NET:networkAt(1, -1, 0)"), lua.eval("NET:networkAt(1, 0, 0)"))


class PickedUpAndSetDown(unittest.TestCase):
    def test_a_part_set_on_an_occupied_square_is_refused(self):
        lua = pumps()
        lua.execute('place("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval('{ place("Test:Spr", 1, 0) }')[2], "occupied")
        self.assertEqual(lua.eval("REG:at(1, 0, 0).type"), "Test:Pipe")

    def test_a_pipe_picked_up_in_the_middle_leaves_two_halves_each_with_its_pump(self):
        lua = pumps()
        lua.execute("""
        place("LiveWater:PondPump", 0, 0) for x = 1, 3 do place("Test:Pipe", x, 0) end place("LiveWater:PondPump", 4, 0)
        place("Test:Spr", 1, 1) place("Test:Spr", 3, 1) NEED["1,1"] = 80 NEED["3,1"] = 80
        """)
        self.assertAlmostEqual(lua.eval("delivered()"), 100)
        lua.execute("TOPO:remove(2, 0, 0)")
        self.assertNotEqual(lua.eval("NET:networkAt(1, 0, 0)"), lua.eval("NET:networkAt(3, 0, 0)"))
        self.assertAlmostEqual(lua.eval("delivered()"), 100, delta=0.2)
        self.assertAlmostEqual(lua.eval("REG:at(0, 0, 0).data.pump.litres"), 50, delta=0.1)
        self.assertAlmostEqual(lua.eval("REG:at(4, 0, 0).data.pump.litres"), 50, delta=0.1)

    def test_the_running_pump_picked_up_then_set_down_again_keeps_its_wear(self):
        lua = pumps()
        lua.execute('place("LiveWater:PondPump", 0, 0, "%s24") place("Test:Spr", 1, 0) NEED["1,0"] = 5' % TILE)
        self.assertEqual(lua.eval("delivered()"), 5)
        worn = lua.eval("REG:at(0, 0, 0).data.pump.efficiency")
        self.assertLess(worn, 100)
        lua.execute("TOPO:remove(0, 0, 0)")
        self.assertEqual(lua.eval("delivered()"), 0)
        lua.execute('PLACEMENT:added("%s24", 0, 0, 0)' % TILE)
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.pump.efficiency"), worn)
        self.assertEqual(lua.eval("delivered()"), 5)

    def test_a_sprinkler_whose_pump_is_picked_up_stops_spraying(self):
        lua = services(new_lua, POND, SPRINKLER)
        lua.execute(SPRINKLER_BENCH)
        lua.execute('LiveWater.Events.on("networkChanged", function(id) CLOCK:settle(id) end)'
                    ' LiveWater.Parts:call(SPR, "open", true) plant(3, 0, 0, 70) CLOCK:tick()')
        self.assertTrue(lua.eval("SPR.data.spray.on"))
        lua.execute("TOPO:remove(0, 0, 0) CLOCK:tick()")
        self.assertFalse(lua.eval("SPR.data.spray.on"))
        self.assertNotEqual(lua.eval("SPR.data.outlet.state"), "served")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "51")

    def test_the_house_inlet_picked_up_with_its_cartridge_brings_it_back(self):
        lua = services(new_lua, POND, INLET)
        lua.execute(FILTER_BENCH)
        lua.execute('place("LiveWater:PondPump", 0, 0, "%s26") place("LiveWater:HouseInlet", 1, 0, "%s40")'
                    ' P.fractions = { ["LiveWater.WaterFilter"] = 0.5 } cmd("fitFilter", 1, 0)' % (TILE, TILE))
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 250)
        sprite = lua.eval("WORLD:sprite(1, 0, 0)")
        lua.execute("TOPO:remove(1, 0, 0)")
        lua.execute('PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function() end, WORLD)'
                    ' PLACEMENT:added("%s", 1, 0, 0)' % sprite)
        self.assertTrue(lua.eval("REG:at(1, 0, 0).data.filter.fitted"))
        self.assertEqual(lua.eval("REG:at(1, 0, 0).data.filter.used"), 250)


class SavedAndLoadedAgain(unittest.TestCase):
    LAYOUT = """
    place("LiveWater:PondPump", 0, 0) for x = 1, 3 do place("Test:Pipe", x, 0) end place("LiveWater:PondPump", 4, 0)
    place("Test:Pipe", 5, 0) WORLD:setEdge(6, 0, 0, false, "wall") place("Test:Pipe", 6, 0) place("Test:Spr", 6, 1)
    place("LiveWater:DripLine", 1, 1) place("LiveWater:DripLine", 2, 1) place("Test:Spr", 1, -1)
    place("LiveWater:BarrelFitting", 3, 1, "batman_livewater_01_64")
    place("LiveWater:BarrelFitting", 3, -1, "batman_livewater_01_64")
    REG:at(3, 1, 0).data.fitting = { mode = "fill", found = true, amount = 0, free = 100, cx = 3, cy = 2, cz = 0 }
    REG:at(3, -1, 0).data.fitting = { mode = "pump", found = true, fluid = "clean", amount = 20, free = 380, cx = 3, cy = -2, cz = 0 }
    NEED = { ["1,1"] = 2, ["2,1"] = 2, ["1,-1"] = 5, ["6,1"] = 5, ["3,1"] = 30 }
    CTX = { need = function(p) return NEED[p.x .. "," .. p.y] or 0 end }
    FLOW = require("LiveWater/LWT_Flow").new(LiveWater.Parts)
    function outcome()
        local out = {}
        for _, id in ipairs(NET:ids()) do
            local r = FLOW:step(NET, id, CTX)
            for key, o in pairs(r.at) do out[key] = o.state .. ":" .. o.litres end
        end
        return out
    end
    """

    def test_the_same_network_steps_the_same_after_a_reload(self):
        lua = services(new_lua, POND, DRIP, FITTING)
        lua.execute(self.LAYOUT)
        before = dict(lua.eval("outcome()").items())
        lua.execute("newServices(STORE) TOPO:rebuild()")
        after = dict(lua.eval("outcome()").items())
        self.assertEqual(after, before)
        self.assertIn("1,1,0", after)
        self.assertNotEqual(lua.eval("NET:networkAt(5, 0, 0)"), lua.eval("NET:networkAt(6, 0, 0)"))


if __name__ == "__main__":
    unittest.main()
