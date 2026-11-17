"""E03: pure network graph (ADR-001 D10, D12-D15): side masks, sprites, ports, valves, merge and split,
pipe distance and service order."""
import unittest

from lwt_harness import new_lua

SETUP = r"""
local sprites = {}
for mask = 0, 15 do sprites[mask] = "t_pipe_" .. mask end
LiveWater.API.registerPart("Test:Pipe", { sprites = sprites, capabilities = { conduit = true } })
LiveWater.API.registerPart("Test:Pump", { sprites = { [0] = "t_pump" }, capabilities = { pump = true, intake = true } })
LiveWater.API.registerPart("Test:SmallPump", { sprites = { [0] = "t_spump" },
    capabilities = { pump = { ports = 1 }, intake = true } })
LiveWater.API.registerPart("Test:Valve", { sprites = { [0] = "t_valve" }, sides = 10,
    capabilities = { conduit = true, valve = true } })
LiveWater.API.registerPart("Test:Spr", { sprites = { [0] = "t_spr" },
    capabilities = { outlet = { type = "sprinkler" } } })
NET = require("LiveWater/LWT_Network").new(LiveWater.Parts)
function put(t, x, y) return NET:add({ type = t, x = x, y = y, z = 0 }) end
"""


def network():
    lua = new_lua("shared/LiveWater/LWT_API.lua")
    lua.execute(SETUP)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Shapes(unittest.TestCase):
    def test_mask_and_sprite_for_the_16_shapes(self):
        offsets = {1: (0, -1), 2: (1, 0), 4: (0, 1), 8: (-1, 0)}
        for mask in range(16):
            lua = network()
            lua.execute('put("Test:Pipe", 10, 10)')
            for bit, (dx, dy) in offsets.items():
                if mask & bit:
                    lua.execute('put("Test:Pipe", %d, %d)' % (10 + dx, 10 + dy))
            self.assertEqual(lua.eval("NET:mask(10, 10, 0)"), mask)
            self.assertEqual(lua.eval("NET:sprite(10, 10, 0)"), "t_pipe_%d" % mask)

    def test_a_part_with_one_sprite_keeps_it_whatever_its_mask(self):
        lua = network()
        lua.execute('put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 2)
        self.assertEqual(lua.eval("NET:sprite(0, 0, 0)"), "t_pump")

    def test_sides_a_part_does_not_offer_are_not_linked(self):
        lua = network()
        lua.execute('put("Test:Valve", 0, 0) put("Test:Pipe", 0, 1) put("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 2)
        self.assertEqual(lua.eval("NET:mask(0, 1, 0)"), 0)
        self.assertNotEqual(lua.eval("NET:networkAt(0, 1, 0)"), lua.eval("NET:networkAt(0, 0, 0)"))

    def test_occupied_square_and_unknown_type_are_refused(self):
        lua = network()
        lua.execute('put("Test:Pipe", 0, 0)')
        self.assertEqual(call(lua, 'put("Test:Pipe", 0, 0)'), (False, "occupied"))
        self.assertEqual(call(lua, 'put("Other:Thing", 5, 5)'), (False, "unknown_part"))


class Ports(unittest.TestCase):
    def test_default_pump_takes_a_pipe_on_each_of_its_four_sides(self):
        lua = network()
        lua.execute('put("Test:Pump", 0, 0)')
        for x, y in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            self.assertTrue(call(lua, 'put("Test:Pipe", %d, %d)' % (x, y))[0])

    def test_connection_beyond_the_ports_is_refused(self):
        lua = network()
        lua.execute('put("Test:SmallPump", 0, 0) put("Test:Pipe", 1, 0)')
        self.assertEqual(call(lua, 'put("Test:Pipe", -1, 0)'), (False, "ports_full"))
        self.assertIsNone(lua.eval("NET:part(-1, 0, 0)"))
        self.assertTrue(call(lua, 'put("Test:Pipe", -1, 1)')[0])


class Valves(unittest.TestCase):
    def test_closed_valve_cuts_downstream(self):
        lua = network()
        lua.execute("""
        put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Valve", 2, 0)
        put("Test:Pipe", 3, 0) put("Test:Spr", 4, 0)
        """)
        net = lua.eval("NET:networkAt(0, 0, 0)")
        self.assertIsNotNone(lua.eval('select(2, NET:reach(%d))["4,0,0"]' % net))
        lua.execute('NET:part(2, 0, 0).data = { valve = { open = false } }')
        reach = lua.eval("select(2, NET:reach(%d))" % net)
        self.assertIsNotNone(reach["2,0,0"])
        self.assertIsNone(reach["3,0,0"])
        self.assertIsNone(reach["4,0,0"])
        self.assertEqual(lua.eval("NET:networkAt(4, 0, 0)"), net)

    def test_water_does_not_cross_a_part_without_conduit(self):
        lua = network()
        lua.execute('put("Test:Pump", 0, 0) put("Test:Spr", 1, 0) put("Test:Pipe", 2, 0)')
        reach = lua.eval("select(2, NET:reach(NET:networkAt(0, 0, 0)))")
        self.assertIsNotNone(reach["1,0,0"])
        self.assertIsNone(reach["2,0,0"])


class MergeAndSplit(unittest.TestCase):
    def test_networks_merge_on_add_and_split_on_remove(self):
        lua = network()
        lua.execute('put("Test:Pump", 0, 0) put("Test:Pipe", 1, 0) put("Test:Pipe", 3, 0) put("Test:Pump", 4, 0)')
        left, right = lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(4, 0, 0)")
        self.assertNotEqual(left, right)
        lua.execute('put("Test:Pipe", 2, 0)')
        merged = lua.eval("NET:networkAt(0, 0, 0)")
        self.assertEqual([lua.eval("NET:networkAt(%d, 0, 0)" % x) for x in range(5)], [merged] * 5)
        self.assertEqual(len(lua.eval("NET:members(%d)" % merged)), 5)
        removed = lua.eval("NET:remove(2, 0, 0)")
        self.assertEqual(removed.type, "Test:Pipe")
        self.assertIsNone(lua.eval("NET:networkAt(2, 0, 0)"))
        a, b = lua.eval("NET:networkAt(1, 0, 0)"), lua.eval("NET:networkAt(3, 0, 0)")
        self.assertNotEqual(a, b)
        self.assertEqual(lua.eval("NET:networkAt(0, 0, 0)"), a)
        self.assertEqual(lua.eval("NET:networkAt(4, 0, 0)"), b)
        self.assertEqual(lua.eval("NET:mask(1, 0, 0)"), 8)

    def test_removing_the_last_part_forgets_its_network(self):
        lua = network()
        lua.execute('put("Test:Pipe", 0, 0)')
        net = lua.eval("NET:networkAt(0, 0, 0)")
        lua.execute("NET:remove(0, 0, 0)")
        self.assertEqual(len(lua.eval("NET:members(%d)" % net)), 0)
        self.assertIsNone(lua.eval("NET:remove(0, 0, 0)"))


class DistanceAndOrder(unittest.TestCase):
    def test_pipe_distance_from_the_nearest_pump(self):
        lua = network()
        lua.execute("""
        put("Test:Pump", 0, 0)
        for x = 1, 5 do put("Test:Pipe", x, 0) end
        put("Test:Pump", 6, 0)
        """)
        reach = lua.eval("select(2, NET:reach(NET:networkAt(0, 0, 0)))")
        self.assertEqual([reach["%d,0,0" % x].dist for x in range(7)], [0, 1, 2, 3, 2, 1, 0])

    def test_service_order_by_distance_then_placement(self):
        lua = network()
        lua.execute("""
        put("Test:Pump", 0, 0)
        put("Test:Pipe", 1, 0) put("Test:Pipe", 2, 0) put("Test:Pipe", -1, 0)
        put("Test:Spr", 2, 1)
        put("Test:Spr", 0, 1)
        put("Test:Spr", 1, -1)
        put("Test:Spr", -1, 1)
        """)
        order = lua.eval("(NET:reach(NET:networkAt(0, 0, 0)))")
        keys = [order[i].key for i in range(1, len(order) + 1)]
        sprinklers = [k for k in keys if k in ("2,1,0", "0,1,0", "1,-1,0", "-1,1,0")]
        self.assertEqual(sprinklers, ["0,1,0", "1,-1,0", "-1,1,0", "2,1,0"])
        self.assertEqual(keys[0], "0,0,0")


if __name__ == "__main__":
    unittest.main()
