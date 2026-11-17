"""E05: persistent global registry (ADR-001 D03, D04, D10): versioned entries, unknown fields kept, parts of an
unregistered type kept and inert, index by coordinates. The store is a plain table standing for the ModData."""
import unittest

from lwt_harness import new_lua

SETUP = r"""
LiveWater.API.registerPart("Test:Pipe", { sprites = { [0] = "t_pipe" }, capabilities = { conduit = true } })
Registry = require("LiveWater/LWT_Registry")
STORE = {}
REG = Registry.new(STORE, LiveWater.Parts)
"""


def registry():
    lua = new_lua("shared/LiveWater/LWT_API.lua")
    lua.execute(SETUP)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Entries(unittest.TestCase):
    def test_entry_is_versioned_and_indexed_by_coordinates(self):
        lua = registry()
        lua.execute('E = REG:add("Test:Pipe", 10, -4, 1)')
        self.assertEqual(lua.eval("E.v"), 1)
        self.assertEqual((lua.eval("E.type"), lua.eval("E.x"), lua.eval("E.y"), lua.eval("E.z")), ("Test:Pipe", 10, -4, 1))
        self.assertTrue(lua.eval('STORE.parts["10,-4,1"] == E'))
        self.assertTrue(lua.eval("REG:at(10, -4, 1) == E"))
        self.assertIsNone(lua.eval("REG:at(10, -4, 0)"))

    def test_occupied_square_and_unregistered_type_are_refused(self):
        lua = registry()
        lua.execute('REG:add("Test:Pipe", 0, 0, 0)')
        self.assertEqual(call(lua, 'REG:add("Test:Pipe", 0, 0, 0)'), (None, "occupied"))
        self.assertEqual(call(lua, 'REG:add("Other:Pipe", 1, 0, 0)'), (None, "unknown_part"))

    def test_placement_order_is_kept_and_never_reused(self):
        lua = registry()
        lua.execute("""
        A = REG:add("Test:Pipe", 0, 0, 0) B = REG:add("Test:Pipe", 1, 0, 0)
        REMOVED = REG:remove(1, 0, 0)
        C = REG:add("Test:Pipe", 2, 0, 0)
        """)
        self.assertEqual((lua.eval("A.order"), lua.eval("C.order")), (1, 3))
        self.assertTrue(lua.eval("REMOVED == B"))
        self.assertIsNone(lua.eval('STORE.parts["1,0,0"]'))
        self.assertIsNone(lua.eval("REG:remove(1, 0, 0)"))

    def test_a_reloaded_store_continues(self):
        lua = registry()
        lua.execute("""
        REG:add("Test:Pipe", 0, 0, 0)
        REG2 = Registry.new(STORE, LiveWater.Parts)
        D = REG2:add("Test:Pipe", 5, 5, 0)
        """)
        self.assertEqual(lua.eval("D.order"), 2)
        self.assertEqual(lua.eval("REG2:at(0, 0, 0).type"), "Test:Pipe")


class Compatibility(unittest.TestCase):
    def test_unknown_fields_are_kept(self):
        lua = registry()
        lua.execute("""
        STORE = { future = { a = 1 }, seq = 7, parts = {
            ["3,3,0"] = { v = 4, type = "Test:Pipe", x = 3, y = 3, z = 0, order = 7, colour = "red",
                          data = { meter = { litres = 12 } } } } }
        REG = Registry.new(STORE, LiveWater.Parts)
        REG:add("Test:Pipe", 3, 4, 0)
        REG:remove(3, 4, 0)
        """)
        e = lua.eval("REG:at(3, 3, 0)")
        self.assertEqual((e.v, e.colour, e.data.meter.litres), (4, "red", 12))
        self.assertEqual(lua.eval("STORE.future.a"), 1)
        self.assertEqual(len(lua.eval("REG:active()")), 1)

    def test_part_of_an_unregistered_type_is_kept_inert_and_comes_back_with_its_type(self):
        lua = registry()
        lua.execute("""
        KNOWN = { ["Test:Pipe"] = true }
        CATALOG = { has = function(self, id) return KNOWN[id] == true end }
        STORE = { seq = 2, parts = {
            ["0,0,0"] = { v = 1, type = "Gone:Pump", x = 0, y = 0, z = 0, order = 1, data = { pump = { on = true } } },
            ["1,0,0"] = { v = 1, type = "Test:Pipe", x = 1, y = 0, z = 0, order = 2, data = {} } } }
        REG = Registry.new(STORE, CATALOG)
        """)
        self.assertEqual(lua.eval('REG:at(0, 0, 0).type'), "Gone:Pump")
        self.assertFalse(lua.eval("REG:isActive(REG:at(0, 0, 0))"))
        active = lua.eval("REG:active()")
        self.assertEqual([active[i].type for i in range(1, len(active) + 1)], ["Test:Pipe"])
        self.assertEqual(call(lua, 'REG:add("Test:Pipe", 0, 0, 0)'), (None, "occupied"))
        lua.execute('KNOWN["Gone:Pump"] = true')
        active = lua.eval("REG:active()")
        self.assertEqual([active[i].type for i in range(1, len(active) + 1)], ["Gone:Pump", "Test:Pipe"])
        self.assertTrue(lua.eval("REG:at(0, 0, 0).data.pump.on"))


if __name__ == "__main__":
    unittest.main()
