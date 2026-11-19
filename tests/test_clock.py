"""E07: the ten-minute clock on the authority (ADR-001 D06, D08, D09; ADR-006 D06): every network with a part
where water starts is stepped, loaded or not, the outlet need comes from an injected provider (0 by default), served
outlets announce waterDelivered; the server subscribes exactly one EveryTenMinutes handler and no per-frame
event."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua
from test_placement import GAME

SETUP = r"""
NEED = {}
function needOf(part) return NEED[part.x .. "," .. part.y] or 0 end
function newClock(need)
    CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
        catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, need = need })
end
newClock(needOf)
function ids(list) local out = {} for i, v in ipairs(list) do out[i] = v end table.sort(out) return out end
"""


def bench():
    lua = services(new_lua)
    lua.execute(SETUP)
    return lua


class Step(unittest.TestCase):
    def test_served_outlets_announce_the_water_delivered(self):
        lua = bench()
        lua.execute("""
        place("Test:Pump", 0, 0) place("Test:Pipe", 1, 0) place("Test:Spr", 2, 0)
        NEED["2,0"] = 3
        EMITTED = {}
        STEPPED = CLOCK:tick()
        """)
        self.assertEqual(len(lua.eval("STEPPED")), 1)
        delivered = lua.eval('emitted("waterDelivered")')
        self.assertEqual(len(delivered), 1)
        e = delivered[1]
        self.assertEqual((e[2].x, e[3], e[4]), (2, 3, "tainted"))

    def test_every_network_with_a_pump_is_stepped_loaded_or_not(self):
        # ADR-006 D06: an unloaded network keeps running; a network without any part where water starts does not
        lua = bench()
        lua.execute("""
        place("Test:Pump", 0, 0) place("Test:Spr", 1, 0)
        place("Test:Pump", 10, 0) place("Test:Spr", 11, 0)
        place("Test:Pipe", 20, 0)
        NEED["1,0"], NEED["11,0"] = 1, 1
        WORLD.unloaded["10,0,0"] = true WORLD.unloaded["11,0,0"] = true
        STEPPED = CLOCK:tick()
        """)
        self.assertEqual(list(lua.eval("ids(STEPPED)").values()),
                         sorted([lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(10, 0, 0)")]))
        self.assertEqual(len(lua.eval('emitted("waterDelivered")')), 2)

    def test_default_need_delivers_nothing(self):
        lua = bench()
        lua.execute("""
        newClock(nil)
        place("Test:Pump", 0, 0) place("Test:Spr", 1, 0)
        STEPPED = CLOCK:tick()
        """)
        self.assertEqual(len(lua.eval("STEPPED")), 1)
        self.assertEqual(len(lua.eval('emitted("waterDelivered")')), 0)


class Wiring(unittest.TestCase):
    def test_one_ten_minute_subscriber_and_no_per_frame_event(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", "shared/LiveWater/Parts/LWT_PartPipe.lua")
        lua.execute(GAME)
        lua.execute('require("LiveWater/LWT_Server")')
        self.assertEqual(lua.eval("#Events.EveryTenMinutes.handlers"), 1)
        for name in ("OnTick", "OnTickEvenPaused", "OnPlayerUpdate", "OnRenderTick", "OnPostRender", "OnPreUIDraw"):
            self.assertEqual(lua.eval("#Events.%s.handlers" % name), 0, name)
        lua.execute('fire("OnInitGlobalModData", true) fire("EveryTenMinutes")')
        self.assertTrue(lua.eval("LiveWater.Server.clock ~= nil"))


if __name__ == "__main__":
    unittest.main()
