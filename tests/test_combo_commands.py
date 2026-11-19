"""Players send commands the authority must refuse or survive (ADR-001 D10, D17, D26; ADR-005 D01): a filter on a pump,
a filter without a cartridge, a valve from too far, two commands on one part in the
same ten minutes. Nothing the client sends is trusted (LWT_Commands)."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua
from test_filter import BENCH as FILTER_BENCH, INLET, POND, TILE

VALVE = "shared/LiveWater/Parts/LWT_PartValve.lua"

COMMANDS = r"""
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS, publisher = PUB,
    events = LiveWater.Events })
CMDS:register("fitFilter", require("LiveWater/Commands/LWT_CmdFitFilter"))
CMDS:register("switchValve", require("LiveWater/Commands/LWT_CmdSwitchValve"))
place("LiveWater:PondPump", 0, 0, "%s26") place("LiveWater:HouseInlet", 1, 0, "%s40")
place("LiveWater:Valve", 0, -1, "%s17") place("Test:Spr", 0, -2) NEED["0,-2"] = 5
""" % (TILE, TILE, TILE)


def bench():
    lua = services(new_lua, POND, INLET, VALVE)
    lua.execute(FILTER_BENCH)
    lua.execute(COMMANDS)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Refusals(unittest.TestCase):
    def test_a_filter_fitted_on_the_pump_is_refused_and_kept(self):
        lua = bench()
        self.assertEqual(call(lua, 'cmd("fitFilter", 0, 0)'), (False, "no_filter_slot"))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 2)

    def test_a_filter_fitted_on_the_inlet_without_a_cartridge_is_refused(self):
        lua = bench()
        lua.execute('P.items["LiveWater.WaterFilter"] = 0')
        self.assertEqual(call(lua, 'cmd("fitFilter", 1, 0)'), (False, "no_cartridge"))
        self.assertFalse(lua.eval("REG:at(1, 0, 0).data.filter and REG:at(1, 0, 0).data.filter.fitted or false"))

    def test_a_valve_switched_from_too_far_stays_as_it_is(self):
        lua = bench()
        lua.execute("P.x, P.y = 9, 9")
        self.assertEqual(call(lua, 'cmd("switchValve", 0, -1)'), (False, "too_far"))
        self.assertTrue(lua.eval('LiveWater.Parts:first(REG:at(0, -1, 0), "opened")'))

    def test_arguments_that_are_not_whole_numbers_are_refused(self):
        lua = bench()
        self.assertEqual(call(lua, 'CMDS:dispatch(P, "switchValve", { x = 0.5, y = -1, z = 0 })'), (False, "invalid"))
        self.assertEqual(call(lua, 'CMDS:dispatch(P, "fitFilter", { x = "1", y = 0, z = 0 })'), (False, "invalid"))


class TwoCommandsInOneStep(unittest.TestCase):
    def test_a_valve_switched_twice_is_back_as_it_was_and_the_water_still_flows(self):
        lua = bench()
        lua.execute('EMITTED = {} cmd("switchValve", 0, -1) cmd("switchValve", 0, -1)')
        self.assertTrue(lua.eval('LiveWater.Parts:first(REG:at(0, -1, 0), "opened")'))
        self.assertEqual(lua.eval('#emitted("valveChanged")'), 2)
        lua.execute("EMITTED = {} CLOCK:tick()")
        self.assertEqual(lua.eval('REG:at(0, -2, 0).data.outlet.state'), "served")

    def test_two_filters_fitted_in_a_row_leave_one_in_and_give_the_first_back(self):
        lua = bench()
        lua.execute('cmd("fitFilter", 1, 0) cmd("fitFilter", 1, 0)')
        self.assertTrue(lua.eval("REG:at(1, 0, 0).data.filter.fitted"))
        self.assertEqual(lua.eval('P.items["LiveWater.WaterFilter"]'), 1)
        self.assertEqual(lua.eval("#P.given"), 1)


if __name__ == "__main__":
    unittest.main()
