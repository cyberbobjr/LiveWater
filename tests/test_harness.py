"""The offline bench itself: game stubs and require, as later tests rely on them."""
import unittest

from lwt_harness import new_lua


class Harness(unittest.TestCase):
    def test_events_add_fire_and_remove(self):
        lua = new_lua()
        lua.execute("""
        N = 0
        local fn = function(k) N = N + k end
        Events.EveryTenMinutes.Add(fn)
        fire("EveryTenMinutes", 2)
        Events.EveryTenMinutes.Remove(fn)
        fire("EveryTenMinutes", 5)
        """)
        self.assertEqual(lua.eval("N"), 2)

    def test_require_of_an_unknown_module_returns_nil(self):
        self.assertIsNone(new_lua().eval("require('LiveWater/Nothing')"))


if __name__ == "__main__":
    unittest.main()
