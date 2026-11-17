"""E07: sprites recomputed from the side mask after every topology change (ADR-001 D11, D12), applied to the
part and its four neighbours only when they change, through the sprite port (fake world here)."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua


def world():
    return services(new_lua)


class Shapes(unittest.TestCase):
    def test_a_lone_pipe_shows_mask_0_and_its_neighbour_follows_a_new_pipe(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pipe_0")
        lua.execute('place("Test:Pipe", 1, 0)')
        # (0,0) links east (2), (1,0) links west (8)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pipe_2")
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), "t_pipe_8")

    def test_a_cross_and_its_removal(self):
        lua = world()
        lua.execute("""
        place("Test:Pipe", 0, 0)
        place("Test:Pipe", 0, -1) place("Test:Pipe", 1, 0) place("Test:Pipe", 0, 1) place("Test:Pipe", -1, 0)
        """)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pipe_15")
        self.assertEqual(lua.eval("WORLD:sprite(0, -1, 0)"), "t_pipe_4")
        lua.execute("TOPO:remove(1, 0, 0) WORLD:removePart(1, 0, 0, 'Test:Pipe')")
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pipe_13")

    def test_only_changed_sprites_are_applied(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 1, 0)')
        lua.execute("WORLD.sets = 0")
        # a pipe far away changes nobody else
        lua.execute('place("Test:Pipe", 10, 10)')
        self.assertEqual(lua.eval("WORLD.sets"), 0)
        self.assertEqual(lua.eval("SPRITES:around(0, 0, 0)"), 0)

    def test_a_part_without_a_sprite_for_its_mask_keeps_the_sprite_it_was_placed_with(self):
        lua = world()
        lua.execute('place("Test:Pump", 0, 0, "t_pump") place("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pump")
        self.assertEqual(lua.eval("WORLD:sprite(1, 0, 0)"), "t_pipe_8")

    def test_an_unloaded_or_missing_object_is_skipped(self):
        lua = world()
        lua.execute("""
        place("Test:Pipe", 0, 0)
        WORLD.unloaded["1,0,0"] = true
        TOPO:add("Test:Pipe", 1, 0, 0)
        """)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pipe_2")
        self.assertEqual(lua.eval("WORLD.sets"), 1)


if __name__ == "__main__":
    unittest.main()
