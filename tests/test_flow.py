"""E04: one pure ten-minute distribution step (ADR-001 D09, D14-D17): pressure budget, flow, water quality,
filter wear, outlets without need."""
import unittest

from lwt_harness import new_lua

SETUP = r"""
local function part(id, caps) LiveWater.API.registerPart(id, { sprites = { [0] = "t_" .. id }, capabilities = caps }) end
part("Test:Pipe", { conduit = true })
part("Test:Pump", { intake = true, pump = true })
part("Test:CleanPump", { intake = { quality = "clean" }, pump = true })
part("Test:FilterPump", { intake = true, pump = true, filter = { capacity = 100 } })
part("Test:InlineFilter", { conduit = true, filter = true })
part("Test:Inlet", { outlet = { type = "houseInlet" } })
part("Test:Spr", { outlet = { type = "sprinkler" } })
part("Test:ClosedSpr", { outlet = { type = "sprinkler" }, valve = { open = false } })
NET = require("LiveWater/LWT_Network").new(LiveWater.Parts)
FLOW = require("LiveWater/LWT_Flow").new(LiveWater.Parts)
NEED = {}
CTX = { need = function(p) return NEED[p.x .. "," .. p.y] end }
function put(t, x, y, need) NET:add({ type = t, x = x, y = y, z = 0 }) NEED[x .. "," .. y] = need end
function step() R = FLOW:step(NET, NET:networkAt(0, 0, 0), CTX) return R end
function state(x, y) return R.at[x .. "," .. y .. ",0"].state end
function litres(x, y) return R.at[x .. "," .. y .. ",0"].litres end
"""


def flow(layout):
    lua = new_lua("shared/LiveWater/LWT_API.lua")
    lua.execute(SETUP)
    lua.execute(layout)
    lua.execute("step()")
    return lua


class Pressure(unittest.TestCase):
    def test_budget_served_nearest_first_the_rest_without_pressure(self):
        lua = flow("""
        put("Test:CleanPump", 0, 0)
        for x = 1, 4 do put("Test:Pipe", x, 0) end
        for x = 4, 1, -1 do put("Test:Inlet", x, 1, 5) end
        put("Test:Spr", 4, -1, 1)
        """)
        self.assertEqual([lua.eval("state(%d, 1)" % x) for x in range(1, 5)],
                         ["served", "served", "served", "no_pressure"])
        self.assertEqual(lua.eval("state(4, -1)"), "no_pressure")
        order = lua.eval("R.outlets")
        self.assertEqual([order[i].key for i in range(1, 6)], ["1,1,0", "2,1,0", "3,1,0", "4,1,0", "4,-1,0"])
        self.assertEqual(lua.eval("R.pressure"), 6)

    def test_cheaper_outlets_fit_the_budget(self):
        lua = flow("""
        put("Test:CleanPump", 0, 0)
        for x = 1, 6 do put("Test:Pipe", x, 0) put("Test:Spr", x, 1, 1) end
        put("Test:Spr", 7, 0, 1)
        """)
        self.assertEqual([lua.eval("state(%d, 1)" % x) for x in range(1, 7)], ["served"] * 6)
        self.assertEqual(lua.eval("state(7, 0)"), "no_pressure")


class Flow(unittest.TestCase):
    def test_one_pond_pump_gives_50_litres_per_step(self):
        lua = flow('put("Test:CleanPump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Inlet", 2, 0, 1000)')
        self.assertEqual(lua.eval("R.water"), 50)
        self.assertEqual(lua.eval("litres(2, 0)"), 50)

    def test_pumps_of_one_network_add_up(self):
        lua = flow("""
        put("Test:CleanPump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Inlet", 2, 0, 1000)
        put("Test:Pipe", 1, 1) put("Test:CleanPump", 1, 2)
        """)
        self.assertEqual((lua.eval("R.water"), lua.eval("R.pressure")), (100, 12))
        self.assertEqual(lua.eval("litres(2, 0)"), 100)

    def test_water_is_shared_nearest_first(self):
        lua = flow("""
        put("Test:CleanPump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Pipe", 2, 0)
        put("Test:Spr", 1, 1, 30) put("Test:Spr", 2, 1, 30)
        """)
        self.assertEqual((lua.eval("litres(1, 1)"), lua.eval("litres(2, 1)")), (30, 20))


class Quality(unittest.TestCase):
    def test_tainted_water_refused_by_house_inlet_without_filter_accepted_by_sprinkler(self):
        lua = flow("""
        put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0)
        put("Test:Inlet", 1, 1, 25) put("Test:Spr", 1, -1, 2)
        """)
        self.assertEqual((lua.eval("state(1, 1)"), lua.eval("litres(1, 1)")), ("unfiltered", 0))
        self.assertEqual(lua.eval("state(1, -1)"), "served")
        self.assertEqual(lua.eval('R.at["1,-1,0"].quality'), "tainted")
        self.assertEqual(lua.eval("R.quality"), "tainted")

    def test_unfiltered_outlet_takes_no_pressure(self):
        lua = flow("""
        put("Test:Pump", 0, 0)
        for x = 1, 3 do put("Test:Pipe", x, 0) end
        for x = 1, 2 do put("Test:Inlet", x, 1, 5) put("Test:Inlet", x, -1, 5) end
        put("Test:Spr", 3, 1, 1) put("Test:Spr", 3, -1, 1)
        """)
        self.assertEqual(lua.eval("state(2, -1)"), "unfiltered")
        self.assertEqual([lua.eval("state(3, 1)"), lua.eval("state(3, -1)")], ["served", "served"])

    def test_filter_on_the_pump_purifies_and_wears_by_volume(self):
        lua = flow('put("Test:FilterPump", 0, 0) put("Test:Inlet", 1, 0, 1000)')
        self.assertEqual(lua.eval("state(1, 0)"), "served")
        self.assertEqual(lua.eval('R.at["1,0,0"].quality'), "clean")
        self.assertEqual(lua.eval("NET:part(0, 0, 0).data.filter.used"), 50)
        lua.execute("step()")
        self.assertEqual(lua.eval("NET:part(0, 0, 0).data.filter.used"), 100)
        lua.execute("step()")
        self.assertEqual(lua.eval("state(1, 0)"), "unfiltered")
        self.assertEqual(lua.eval("NET:part(0, 0, 0).data.filter.used"), 100)

    def test_inline_filter_purifies_only_what_goes_through_it(self):
        lua = flow("""
        put("Test:Pump", 0, 0) put("Test:InlineFilter", 1, 0) put("Test:Inlet", 2, 0, 10)
        put("Test:Spr", -1, 0, 1)
        """)
        self.assertEqual(lua.eval('R.at["2,0,0"].quality'), "clean")
        self.assertEqual(lua.eval('R.at["-1,0,0"].quality'), "tainted")
        self.assertEqual(lua.eval("NET:part(1, 0, 0).data.filter.used"), 10)


class Need(unittest.TestCase):
    def test_outlets_without_need_are_not_served_and_take_nothing(self):
        lua = flow("""
        put("Test:CleanPump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Pipe", 2, 0) put("Test:Pipe", 3, 0)
        put("Test:Inlet", 1, 1, 0) put("Test:Inlet", 2, 1) put("Test:Inlet", 3, 1, 5) put("Test:Inlet", 3, -1, 5)
        put("Test:Inlet", 2, -1, 5)
        """)
        self.assertEqual(lua.eval("state(1, 1)"), "idle")
        self.assertEqual(lua.eval("state(2, 1)"), "idle")
        self.assertEqual(lua.eval("litres(1, 1)"), 0)
        self.assertEqual([lua.eval("state(2, -1)"), lua.eval("state(3, 1)"), lua.eval("state(3, -1)")],
                         ["served", "served", "served"])

    def test_closed_outlet_is_not_served(self):
        lua = flow('put("Test:CleanPump", 0, 0) put("Test:ClosedSpr", 1, 0, 5)')
        self.assertEqual((lua.eval("state(1, 0)"), lua.eval("litres(1, 0)")), ("closed", 0))


if __name__ == "__main__":
    unittest.main()
