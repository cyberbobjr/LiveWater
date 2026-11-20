"""E02: public API (LiveWater.API), part and capability registries, events (ADR-001 D01-D07)."""
import unittest

from lwt_harness import new_lua

API = "shared/LiveWater/LWT_API.lua"
PIPE = '{ sprites = { [0] = "t_pipe_0", [5] = "t_pipe_5" }, capabilities = { conduit = true } }'


def api():
    lua = new_lua(API)
    lua.execute("LOG = {} print = function(s) LOG[#LOG + 1] = s end")
    return lua


def call(lua, expr):
    """(first, second) results of a Lua call."""
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


def register(lua, pid, definition):
    return call(lua, "LiveWater.API.registerPart(%r, %s)" % (pid, definition))


class RegisterPart(unittest.TestCase):
    def test_valid_definition_is_accepted_and_described(self):
        lua = api()
        self.assertEqual(register(lua, "Test:Pipe", PIPE), (True, None))
        d = lua.eval('LiveWater.API.part("Test:Pipe")')
        self.assertEqual(d.sprites[0], "t_pipe_0")
        self.assertEqual(d.sprites[5], "t_pipe_5")
        self.assertEqual(d.sides, 15)
        self.assertIsNotNone(d.capabilities.conduit)
        self.assertIsNone(lua.eval('LiveWater.API.part("Test:Nothing")'))

    def test_pump_defaults_come_from_the_adr(self):
        lua = api()
        register(lua, "Test:Pump", '{ sprites = { [0] = "t_pump" }, capabilities = { pump = true, intake = {} } }')
        d = lua.eval('LiveWater.API.part("Test:Pump")')
        self.assertEqual((d.capabilities.pump.ports, d.capabilities.pump.pressure, d.capabilities.pump.flow), (4, 6, 50))
        self.assertEqual(d.capabilities.intake.quality, "tainted")

    def test_outlet_defaults_depend_on_its_type_and_can_be_tuned(self):
        lua = api()
        register(lua, "Test:Inlet", '{ sprites = { [0] = "t_in" }, capabilities = { outlet = { type = "houseInlet" } } }')
        register(lua, "Test:Spr", '{ sprites = { [0] = "t_spr" }, capabilities = { outlet = { type = "sprinkler" } } }')
        register(lua, "Test:Big", '{ sprites = { [0] = "t_big" }, capabilities = { outlet = { type = "sprinkler", pressureCost = 3 } } }')
        inlet = lua.eval('LiveWater.API.part("Test:Inlet")').capabilities.outlet
        spr = lua.eval('LiveWater.API.part("Test:Spr")').capabilities.outlet
        big = lua.eval('LiveWater.API.part("Test:Big")').capabilities.outlet
        self.assertEqual((inlet.pressureCost, inlet.needsClean), (2, True))
        self.assertEqual((spr.pressureCost, spr.needsClean), (1, False))
        self.assertEqual(big.pressureCost, 3)

    def test_every_starting_capability_kind_is_registered(self):
        lua = api()
        for kind in ("conduit", "intake", "pump", "valve", "filter", "outlet", "controller"):
            params = '{ type = "sprinkler" }' if kind == "outlet" else "true"
            ok, why = register(lua, "Test:%s" % kind.capitalize(),
                               '{ sprites = { [0] = "t_%s" }, capabilities = { %s = %s } }' % (kind, kind, params))
            self.assertEqual((ok, why), (True, None), kind)

    def test_identifier_outside_a_namespace_is_refused(self):
        lua = api()
        for pid in ("Pipe", "Test:", ":Pipe", "Te st:Pipe", "Test:Pi:pe"):
            self.assertEqual(register(lua, pid, PIPE), (False, "invalid_id"), pid)
        self.assertEqual(call(lua, "LiveWater.API.registerPart(12, %s)" % PIPE), (False, "invalid_id"))

    def test_duplicate_id_and_duplicate_sprite_are_refused(self):
        lua = api()
        register(lua, "Test:Pipe", PIPE)
        self.assertEqual(register(lua, "Test:Pipe", '{ sprites = { [0] = "other" }, capabilities = { conduit = true } }'),
                         (False, "duplicate_part"))
        self.assertEqual(register(lua, "Test:Copy", '{ sprites = { [3] = "t_pipe_5" }, capabilities = { conduit = true } }'),
                         (False, "duplicate_sprite"))
        self.assertIsNone(lua.eval('LiveWater.API.part("Test:Copy")'))

    def test_unknown_capability_is_refused(self):
        lua = api()
        self.assertEqual(register(lua, "Test:Odd", '{ sprites = { [0] = "t" }, capabilities = { teleport = true } }'),
                         (False, "unknown_capability"))

    def test_invalid_fields_are_refused_with_a_reason(self):
        lua = api()
        cases = {
            "nil": "invalid_definition",
            '{ capabilities = { conduit = true } }': "invalid_sprites",
            '{ sprites = { [16] = "t" }, capabilities = { conduit = true } }': "invalid_sprites",
            '{ sprites = { [0] = 5 }, capabilities = { conduit = true } }': "invalid_sprites",
            '{ sprites = { [0] = "t" }, sides = 16, capabilities = { conduit = true } }': "invalid_sides",
            '{ sprites = { [0] = "t" } }': "invalid_capabilities",
            '{ sprites = { [0] = "t" }, capabilities = {} }': "invalid_capabilities",
            '{ sprites = { [0] = "t" }, capabilities = { pump = { ports = 0 } } }': "invalid_field",
            '{ sprites = { [0] = "t" }, capabilities = { pump = { pressure = "high" } } }': "invalid_field",
            '{ sprites = { [0] = "t" }, capabilities = { outlet = {} } }': "invalid_field",
            '{ sprites = { [0] = "t" }, capabilities = { valve = 3 } }': "invalid_field",
        }
        for definition, reason in cases.items():
            self.assertEqual(register(lua, "Test:Bad", definition), (False, reason), definition)

    def test_refusal_prints_an_english_warning(self):
        lua = api()
        register(lua, "Test:Odd", '{ sprites = { [0] = "t" }, capabilities = { teleport = true } }')
        line = lua.eval("LOG[1]")
        self.assertIn("Test:Odd", line)
        self.assertIn("unknown_capability", line)
        self.assertIn("refused", line)

    def test_definition_is_copied_by_whitelist(self):
        lua = api()
        lua.execute("""
        DEF = { sprites = { [0] = "t_pump" }, extra = 1,
                capabilities = { pump = { ports = 2, secret = true } } }
        LiveWater.API.registerPart("Test:Pump", DEF)
        DEF.sprites[0] = "hacked"
        DEF.capabilities.pump.ports = 1
        local copy = LiveWater.API.part("Test:Pump")
        copy.capabilities.pump.ports = 3
        """)
        d = lua.eval('LiveWater.API.part("Test:Pump")')
        self.assertEqual(d.sprites[0], "t_pump")
        self.assertEqual(d.capabilities.pump.ports, 2)
        self.assertIsNone(d.extra)
        self.assertIsNone(d.capabilities.pump.secret)

    def test_registries_are_sealed_on_init_global_mod_data(self):
        lua = api()
        lua.execute('fire("OnInitGlobalModData", false)')
        self.assertEqual(register(lua, "Test:Pipe", PIPE), (False, "registration_closed"))
        self.assertEqual(call(lua, 'LiveWater.API.registerCapability("gauge", { define = function() return {} end })'),
                         (False, "registration_closed"))

    def test_revision(self):
        self.assertEqual(api().eval("LiveWater.API.revision"), 25)


class RegisterCapability(unittest.TestCase):
    def test_a_new_capability_can_be_used_by_a_part(self):
        lua = api()
        self.assertEqual(call(lua, 'LiveWater.API.registerCapability("gauge", { define = function(p) return {} end })'),
                         (True, None))
        self.assertEqual(register(lua, "Test:Gauge", '{ sprites = { [0] = "t_m" }, capabilities = { gauge = true } }'),
                         (True, None))

    def test_invalid_or_duplicate_capability_is_refused(self):
        lua = api()
        ok = "{ define = function(p) return {} end }"
        self.assertEqual(call(lua, 'LiveWater.API.registerCapability("valve", %s)' % ok), (False, "duplicate_capability"))
        self.assertEqual(call(lua, 'LiveWater.API.registerCapability("bad kind", %s)' % ok), (False, "invalid_kind"))
        self.assertEqual(call(lua, 'LiveWater.API.registerCapability("gauge", {})'), (False, "invalid_implementation"))
        self.assertEqual(call(lua, 'LiveWater.API.registerCapability("gauge", { define = "nope" })'),
                         (False, "invalid_implementation"))


class PublicEvents(unittest.TestCase):
    def test_subscribe_emit_and_unsubscribe(self):
        lua = api()
        lua.execute("""
        GOT = {}
        FN = function(id, litres, quality) GOT[#GOT + 1] = id .. ":" .. litres .. ":" .. quality end
        LiveWater.Events.on("waterDelivered", FN)
        LiveWater.Events.on("waterDelivered", FN)
        LiveWater.Events.emit("waterDelivered", "a", 25, "clean")
        LiveWater.Events.off("waterDelivered", FN)
        LiveWater.Events.emit("waterDelivered", "b", 5, "tainted")
        """)
        self.assertEqual(list(lua.eval("GOT").values()), ["a:25:clean"])

    def test_every_adr_event_exists_and_unknown_names_are_refused(self):
        lua = api()
        for name in ("partAdded", "partRemoved", "networkChanged", "waterDelivered", "valveChanged"):
            self.assertEqual(call(lua, 'LiveWater.Events.on(%r, function() end)' % name), (True, None), name)
        self.assertEqual(call(lua, 'LiveWater.Events.on("partExploded", function() end)'), (False, "unknown_event"))
        self.assertEqual(call(lua, 'LiveWater.Events.on("partAdded", 3)'), (False, "invalid_handler"))


if __name__ == "__main__":
    unittest.main()
