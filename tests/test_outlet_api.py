"""ADR-012 D04: open consumer API. LiveWater.API.registerOutlet(type, handler) tells where the water of a kind of
outlet goes: need(part), deliver(part, litres, quality), optional release(part) and cut(part). The authority builds its
outlet handlers from LiveWater's own consumers and from this registry (API revision 22)."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua

API = "shared/LiveWater/LWT_API.lua"

TROUGH = r"""
TROUGH = { given = {} }
function TROUGH:need(part) return 30 end
function TROUGH:deliver(part, litres, quality) table.insert(self.given, { x = part.x, litres = litres, quality = quality }) end
"""


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


def api():
    lua = new_lua(API)
    lua.execute("LOG = {} print = function(s) LOG[#LOG + 1] = s end")
    lua.execute(TROUGH)
    return lua


class RegisterOutlet(unittest.TestCase):
    def test_revision_22_or_later(self):
        self.assertGreaterEqual(api().eval("LiveWater.API.revision"), 22)

    def test_a_mod_registers_its_consumer_once(self):
        lua = api()
        self.assertEqual(call(lua, 'LiveWater.API.registerOutlet("Test:Trough", TROUGH)'), (True, None))
        self.assertEqual(call(lua, 'LiveWater.API.registerOutlet("Test:Trough", TROUGH)'), (False, "duplicate_outlet"))

    def test_the_types_of_livewater_are_taken(self):
        lua = api()
        for name in ("houseInlet", "sprinkler", "drip", "barrelFill"):
            self.assertEqual(call(lua, 'LiveWater.API.registerOutlet("%s", TROUGH)' % name), (False, "duplicate_outlet"))

    def test_bad_type_or_handler_is_refused(self):
        lua = api()
        self.assertEqual(call(lua, 'LiveWater.API.registerOutlet("bad type", TROUGH)'), (False, "invalid_type"))
        for handler in ("nil", "42", "{ need = function() end }", "{ deliver = function() end }",
                        "{ need = 1, deliver = function() end }",
                        "{ need = function() end, deliver = function() end, release = true }",
                        "{ need = function() end, deliver = function() end, cut = 'x' }"):
            self.assertEqual(call(lua, 'LiveWater.API.registerOutlet("Test:T", %s)' % handler),
                             (False, "invalid_handler"), handler)
        self.assertTrue(any("registerOutlet" in line for line in lua.eval("LOG").values()))

    def test_closed_after_the_world_starts(self):
        lua = api()
        lua.execute('fire("OnInitGlobalModData", false)')
        self.assertEqual(call(lua, 'LiveWater.API.registerOutlet("Test:Trough", TROUGH)'), (False, "registration_closed"))


BENCH = TROUGH + r"""
LiveWater.API.registerOutlet("Test:Trough", TROUGH)
LiveWater.API.registerPart("Test:TroughPart", { sprites = { [0] = "t_trough" },
    capabilities = { outlet = { type = "Test:Trough" } } })
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
OUTLETS:adopt(LiveWater.OutletTypes)
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, sources = LiveWater.Sources,
    power = { powered = function() return true end }, need = function(part) return OUTLETS:need(part) end })
place("Test:Pump", 0, 0) place("Test:Pipe", 1, 0) place("Test:TroughPart", 2, 0)
"""


class ThirdPartyConsumer(unittest.TestCase):
    def test_the_handler_gets_the_water_after_a_step_with_a_pump(self):
        lua = services(new_lua)
        lua.execute(BENCH)
        lua.execute("CLOCK:tick()")
        given = lua.eval("TROUGH.given")
        self.assertEqual(len(given), 1)
        self.assertEqual((given[1].x, given[1].litres, given[1].quality), (2, 30, "tainted"))
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.outlet.state"), "served")

    def test_livewater_own_handlers_keep_their_types(self):
        lua = services(new_lua)
        lua.execute(BENCH)
        self.assertEqual(call(lua, "OUTLETS:register('Test:Trough', TROUGH)"), (False, "duplicate_outlet"))
        self.assertEqual(call(lua, "OUTLETS:register('sprinkler', TROUGH)"), (True, None))
        self.assertEqual(call(lua, "OUTLETS:register('drip', { need = 1 })"), (False, "invalid_handler"))


if __name__ == "__main__":
    unittest.main()
