"""ADR-017 (plan-017 E01): the water pump wired to a Live Wire inverter. With Live Wire API revision 9 or later the
part types whose definition carries `link` (the pond pump, Electrical 2) register as consumers wired by electric wire;
the automatic sprinkler timer stays on the current of its square; revisions 6 to 8 register as before. The base
consumer definition is shared: the authority adds its draw, information and summary, a multiplayer client registers
too (its menus find the pump by sprite) with no state and no draw; a single player game registers once. On a square
not loaded, a linked pump follows Live Wire's consumerLinkPowered with the last circuit reading; an unlinked one keeps
the rules of the absence (ADR-006 D07)."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
SPRINKLER = "shared/LiveWater/Parts/LWT_PartSprinkler.lua"
AUTO = "shared/LiveWater/Parts/LWT_PartSprinklerAuto.lua"
CLIENT = "client/LiveWater/LWT_PowerClient.lua"
PUMP_ID = "LiveWater_LiveWater_PondPump"
TIMER_ID = "LiveWater_LiveWater_SprinklerAuto"


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


# Live Wire double: registerConsumer records the definitions; consumerLinkPowered answers LINKED["x,y,z"] (true,
# false, or nil when no wired consumer stands there), from revision 9 only.
LIVEWIRE = r"""
REGISTERED = {}
LINKED = {}
GRID = {}
function fakeLiveWire(revision, withGrid)
    local api = { revision = revision,
        registerConsumer = function(id, def) REGISTERED[id] = def return true end,
        consumerPowered = function(obj) return obj.lw == true end }
    if revision >= 9 then
        api.consumerLinkPowered = function(x, y, z) return LINKED[x .. "," .. y .. "," .. z] end
    end
    if withGrid then api.gridAt = function(x, y, z) return GRID[x .. "," .. y .. "," .. z] end end
    return api
end
"""


class LinkField(unittest.TestCase):
    def test_the_pond_pump_is_linkable_at_electrical_2_and_the_timer_is_not(self):
        lua = new_lua(API, SPRINKLER, POND, AUTO)
        self.assertEqual(lua.eval('LiveWater.Parts:linkOf("LiveWater:PondPump").level'), 2)
        self.assertIsNone(lua.eval('LiveWater.Parts:linkOf("LiveWater:SprinklerAuto")'))
        self.assertEqual(lua.eval('LiveWater.API.part("LiveWater:PondPump").link.level'), 2)

    def test_the_link_level_is_an_integer_from_0_to_10(self):
        lua = new_lua(API)
        lua.execute("print = function() end")
        for i, bad in enumerate(("{ level = 11 }", "{ level = -1 }", "{ level = 1.5 }", "{}", "2")):
            self.assertEqual(call(lua, 'LiveWater.API.registerPart("Test:B%d", { sprites = { [0] = "b%d" },'
                                       ' link = %s, capabilities = { pump = true } })' % (i, i, bad)),
                             (False, "invalid_link"), bad)
        self.assertEqual(call(lua, 'LiveWater.API.registerPart("Test:G", { sprites = { [0] = "g" },'
                                   ' link = { level = 0 }, capabilities = { pump = true } })'), (True, None))
        lua.execute('L = LiveWater.Parts:linkOf("Test:G") L.level = 9')
        self.assertEqual(lua.eval('LiveWater.Parts:linkOf("Test:G").level'), 0)

    def test_revision_24(self):
        self.assertGreaterEqual(new_lua(API).eval("LiveWater.API.revision"), 24)


def authority():
    lua = services(new_lua, SPRINKLER, POND, AUTO)
    lua.execute(LIVEWIRE)
    lua.execute(r"""
    function newPower(api)
        POW = require("LiveWater/LWT_Power").new({ catalog = LiveWater.Parts, world = WORLD })
        return POW:register(api)
    end
    """)
    return lua


class Registration(unittest.TestCase):
    def test_revision_9_wires_the_pump_at_level_2_and_not_the_timer(self):
        lua = authority()
        self.assertEqual(lua.eval("newPower(fakeLiveWire(9))"), 3)
        self.assertEqual(lua.eval("REGISTERED.%s.link.level" % PUMP_ID), 2)
        self.assertIsNone(lua.eval("REGISTERED.%s.link" % TIMER_ID))
        # the authority keeps its draw, information and summary
        for field in ("powerConsumption", "display", "summary"):
            self.assertEqual(lua.eval("type(REGISTERED.%s.%s)" % (PUMP_ID, field)), "function", field)

    def test_revisions_6_to_8_register_without_link(self):
        for revision in (6, 8):
            lua = authority()
            self.assertEqual(lua.eval("newPower(fakeLiveWire(%d))" % revision), 3)
            self.assertIsNone(lua.eval("REGISTERED.%s.link" % PUMP_ID))
            self.assertEqual(lua.eval("REGISTERED.%s.category" % PUMP_ID), "other")
            self.assertEqual(lua.eval("REGISTERED.%s.circuit" % PUMP_ID), "equipment")


def client(is_client):
    lua = new_lua(API, SPRINKLER, POND, AUTO)
    lua.execute(LIVEWIRE)
    lua.execute("isClient = function() return %s end" % ("true" if is_client else "false"))
    lua.execute("LiveWire = { API = fakeLiveWire(9) }")
    lua.execute("LOG = {} print = function(s) LOG[#LOG + 1] = s end")
    lua.execute('require("LiveWater/LWT_PowerClient")')
    return lua


class ClientRegistration(unittest.TestCase):
    def test_a_multiplayer_client_registers_at_on_init_world_without_state(self):
        lua = client(True)
        self.assertIsNone(lua.eval("REGISTERED.%s" % PUMP_ID))
        lua.execute('fire("OnInitWorld")')
        self.assertEqual(lua.eval("REGISTERED.%s.link.level" % PUMP_ID), 2)
        self.assertIsNone(lua.eval("REGISTERED.%s.link" % TIMER_ID))
        self.assertEqual(lua.eval("REGISTERED.%s.powerConsumption({})" % PUMP_ID), 0)
        self.assertIsNone(lua.eval("REGISTERED.%s.display" % PUMP_ID))
        self.assertIsNone(lua.eval("REGISTERED.%s.summary" % PUMP_ID))
        sprites = lua.eval("REGISTERED.%s.sprites" % PUMP_ID)
        self.assertEqual(len(sprites), 8)

    def test_a_single_player_game_registers_from_the_authority_only(self):
        lua = client(False)
        lua.execute('fire("OnInitWorld")')
        self.assertIsNone(lua.eval("REGISTERED.%s" % PUMP_ID))

    def test_without_live_wire_the_client_registers_nothing(self):
        lua = client(True)
        lua.execute('LiveWire = nil fire("OnInitWorld")')
        self.assertIsNone(lua.eval("REGISTERED.%s" % PUMP_ID))


def away_bench(api):
    lua = authority()
    lua.execute(r"""
    place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24")
    PART = REG:at(0, 0, 0)
    function away() WORLD.unloaded["0,0,0"] = true end
    function inverter(on) return { name = "", inverter = { id = 1, model = "m", state = "on", cond = 100,
        maxW = 1000, powered = on } } end
    """)
    lua.execute("newPower(%s)" % api)
    return lua


class UnloadedLinkedPump(unittest.TestCase):
    def test_a_linked_pump_follows_its_inverter_while_unloaded(self):
        lua = away_bench("fakeLiveWire(9, true)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        # wired outside any inverter area: no grid covers the square, the public grid is off
        lua.execute('away() WORLD.gridOff = true LINKED["0,0,0"] = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute('LINKED["0,0,0"] = false GRID["0,0,0"] = inverter(true)')
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_a_circuit_cut_at_the_last_loaded_step_stays_cut(self):
        lua = away_bench("fakeLiveWire(9, true)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = false')
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute('away() LINKED["0,0,0"] = true')
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_an_unlinked_pump_keeps_the_rules_of_the_absence(self):
        lua = away_bench("fakeLiveWire(9, true)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute('away() GRID["0,0,0"] = inverter(true)')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute('GRID["0,0,0"] = inverter(false)')
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute('GRID["0,0,0"] = nil')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute("WORLD.gridOff = true")
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_a_part_type_without_link_never_asks_for_a_wired_consumer(self):
        lua = away_bench("fakeLiveWire(9, true)")
        lua.execute(r"""
        place("LiveWater:SprinklerAuto", 3, 3, "batman_livewater_01_56")
        TIMER = REG:at(3, 3, 0)
        WORLD:object(3, 3, 0, "LiveWater:SprinklerAuto").lw = true
        """)
        self.assertTrue(lua.eval("POW:powered(TIMER)"))
        lua.execute('WORLD.unloaded["3,3,0"] = true LINKED["3,3,0"] = false')
        self.assertTrue(lua.eval("POW:powered(TIMER)"))


if __name__ == "__main__":
    unittest.main()
