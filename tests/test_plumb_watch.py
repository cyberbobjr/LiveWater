"""ADR-018 (plan 018 E01): a fixture plumbed with the wrench (vanilla ISPlumbItem, run on the authority) surveys the
relays around its square and brings one step of the network of every house inlet whose area covers it forward at
once, through the same Clock method as an opened valve (ADR-010 D02), capped by MAX_AHEAD. The vanilla action is
wrapped once; its arguments, results and behaviour are kept."""
import unittest

from test_inlet import TILE, bench as inlet_bench

WATCH = r"""
PlumbWatch = require("LiveWater/LWT_PlumbWatch")
WATCH = PlumbWatch.new({ relays = RELAYS, clock = CLOCK })
-- Double of the vanilla action: complete() plumbs the fixture of the listed index when it can.
FakePlumbItem = { calls = 0 }
function FakePlumbItem.complete(self, extra)
    FakePlumbItem.calls = FakePlumbItem.calls + 1
    FakePlumbItem.extra = extra
    if self.fails then return false end
    PLUMB.list[self.index].plumbed = true
    return true, "kept"
end
-- What the game adapter tells of the action: the square of its fixture once it uses an outside source.
function probe(action)
    local f = PLUMB.list[action.index]
    if f and f.plumbed then return f.x, f.y, f.z end
    return nil
end
function react(x, y, z) STEPPED = WATCH:plumbed(x, y, z) end
WRAPPED = PlumbWatch.wrap(FakePlumbItem, probe, react)
function plumb(index, fails)
    EMITTED = {}
    STEPPED = nil
    local action = setmetatable({ index = index, fails = fails }, { __index = FakePlumbItem })
    return { action:complete("arg") }
end
"""


def bench():
    lua = inlet_bench()
    lua.execute('WORLD.dry["0,9,0"] = true WORLD.near["0,9,0"] = { camping_01_16 = true }')
    # a plumbed sink at (2, 12) and an unplumbed one at (6, 16) in the house; one far away at (60, 60)
    lua.execute('PLUMB:addFixture(2, 12, 0) PLUMB:addFixture(6, 16, 0, false) PLUMB:addFixture(60, 60, 0, false)'
                ' place("LiveWater:PondPump", 0, 9, "%s24")' % TILE)
    for x in range(1, 5):
        lua.execute('place("Test:Pipe", %d, 9)' % x)
    lua.execute('place("LiveWater:HouseInlet", 5, 9, "%s42")' % TILE)
    lua.execute(WATCH)
    lua.execute("CLOCK:tick()")
    return lua


class Plumbed(unittest.TestCase):
    def test_a_fixture_plumbed_in_an_inlet_area_gets_its_water_at_once(self):
        lua = bench()
        self.assertEqual(lua.eval("relayAt(6, 16, 1).amount"), 0)
        scans = lua.eval("PLUMB.scans")
        out = lua.eval("plumb(2)")
        self.assertEqual((out[1], out[2]), (True, "kept"))
        self.assertEqual(lua.eval("FakePlumbItem.extra"), "arg")
        self.assertEqual(lua.eval("PLUMB.scans"), scans + 1)
        self.assertEqual(lua.eval("relayAt(6, 16, 1).amount"), 25)
        self.assertEqual(lua.eval("#STEPPED"), 1)
        self.assertEqual(lua.eval('#emitted("waterDelivered")'), 1)

    def test_the_step_brought_forward_is_skipped_by_the_clock(self):
        lua = bench()
        lua.execute("plumb(2)")
        self.assertEqual(lua.eval("#CLOCK:tick()"), 0)
        self.assertEqual(lua.eval("#CLOCK:tick()"), 1)

    def test_a_failed_action_does_nothing(self):
        lua = bench()
        out = lua.eval("plumb(2, true)")
        self.assertEqual(out[1], False)
        self.assertIsNone(lua.eval("STEPPED"))
        self.assertEqual(lua.eval("relayAt(6, 16, 1).amount"), 0)

    def test_a_fixture_already_plumbed_does_nothing(self):
        lua = bench()
        out = lua.eval("plumb(1)")
        self.assertEqual(out[1], True)
        self.assertIsNone(lua.eval("STEPPED"))
        self.assertEqual(lua.eval("#CLOCK:tick()"), 1)

    def test_a_fixture_outside_every_inlet_area_steps_nothing(self):
        lua = bench()
        lua.execute("plumb(3)")
        self.assertEqual(lua.eval("#STEPPED"), 0)
        self.assertEqual(lua.eval('#emitted("waterDelivered")'), 0)
        self.assertEqual(lua.eval("#CLOCK:tick()"), 1)

    def test_plumbing_brings_at_most_max_ahead_steps_forward_shared_with_the_valves(self):
        lua = bench()
        ahead = lua.eval("require('LiveWater/LWT_Clock').MAX_AHEAD")
        lua.execute("for i = 1, %d do WATCH:plumbed(6, 16, 0) end" % ahead)
        self.assertEqual(lua.eval("#WATCH:plumbed(6, 16, 0)"), 0)
        self.assertEqual(lua.eval("CLOCK:bringForward(CLOCK.network:networkAt(5, 9, 0))"), False)


class Wrapping(unittest.TestCase):
    def test_the_action_is_wrapped_once(self):
        lua = bench()
        self.assertTrue(lua.eval("WRAPPED"))
        lua.execute("FIRST = FakePlumbItem.complete")
        self.assertFalse(lua.eval("PlumbWatch.wrap(FakePlumbItem, probe, react)"))
        self.assertTrue(lua.eval("FakePlumbItem.complete == FIRST"))
        lua.execute("FakePlumbItem.calls = 0 plumb(2)")
        self.assertEqual(lua.eval("FakePlumbItem.calls"), 1)
        self.assertEqual(lua.eval("#STEPPED"), 1)

    def test_no_action_class_wraps_nothing(self):
        lua = bench()
        self.assertFalse(lua.eval("PlumbWatch.wrap(nil, probe, react)"))


class Wiring(unittest.TestCase):
    def test_the_composition_root_wraps_the_vanilla_action_once_per_session(self):
        from lwt_harness import new_lua
        from test_placement import GAME
        lua = new_lua("shared/LiveWater/LWT_API.lua", "shared/LiveWater/Parts/LWT_PartPipe.lua")
        lua.execute(GAME)
        lua.execute("ISPlumbItem = { complete = function() return true end } VANILLA = ISPlumbItem.complete")
        lua.execute('require("LiveWater/LWT_Server")')
        lua.execute('fire("OnInitGlobalModData", true)')
        lua.execute("FIRST = ISPlumbItem.complete")
        self.assertTrue(lua.eval("FIRST ~= VANILLA"))
        lua.execute('fire("OnInitGlobalModData", false)')
        self.assertTrue(lua.eval("ISPlumbItem.complete == FIRST"))
        self.assertTrue(lua.eval("ISPlumbItem.complete({})"))
        self.assertTrue(lua.eval("LiveWater.Server.plumbWatch ~= nil"))


if __name__ == "__main__":
    unittest.main()
