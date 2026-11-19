"""ADR-002: pipes and barriers. A solid wall on the common edge of two squares cuts the link (D01), a fence lets it
through (D02) and the pipe whose own N or W edge carries the fence it crosses is drawn with a sleeve (D03), through
the `edges` port of the graph (D04); a wall or fence set down or taken away later re-links the parts around (D05)."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua


def world():
    return services(new_lua)


def edge(lua, x, y, north, kind):
    lua.execute('WORLD:setEdge(%d, %d, 0, %s, %s)' % (x, y, "true" if north else "false",
                                                      '"%s"' % kind if kind else "nil"))


class Links(unittest.TestCase):
    def test_a_solid_wall_cuts_the_link_on_every_side(self):
        lua = world()
        edge(lua, 0, 1, True, "wall")    # between (0,0) and (0,1): N edge of (0,1)
        edge(lua, 1, 0, False, "wall")   # between (0,0) and (1,0): W edge of (1,0)
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 0, 1) place("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 0)
        self.assertEqual(lua.eval("NET:mask(0, 1, 0)"), 0)
        self.assertEqual(lua.eval("NET:mask(1, 0, 0)"), 0)
        self.assertNotEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(0, 1, 0)"))

    def test_a_fence_lets_the_pipe_through(self):
        lua = world()
        edge(lua, 0, 1, True, "fence")
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 0, 1)')
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 4)
        self.assertEqual(lua.eval("NET:mask(0, 1, 0)"), 1)

    def test_without_an_edges_port_nothing_cuts(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua")
        lua.execute("""
        local s = {} for m = 0, 15 do s[m] = "p" .. m end
        LiveWater.API.registerPart("T:P", { sprites = s, capabilities = { conduit = true } })
        N = require("LiveWater/LWT_Network").new(LiveWater.Parts)
        N:add({ type = "T:P", x = 0, y = 0, z = 0 }) N:add({ type = "T:P", x = 0, y = 1, z = 0 })
        """)
        self.assertEqual(lua.eval("N:mask(0, 0, 0)"), 4)


class Sleeves(unittest.TestCase):
    def test_the_pipe_that_carries_the_fence_draws_the_sleeve(self):
        lua = world()
        edge(lua, 0, 1, True, "fence")
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 0, 1)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 1, 0)"), "t_pipe_1_x1")
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pipe_4")

    def test_north_and_west_fences_together(self):
        lua = world()
        edge(lua, 1, 1, True, "fence")
        edge(lua, 1, 1, False, "fence")
        lua.execute('place("Test:Pipe", 1, 1) place("Test:Pipe", 1, 0) place("Test:Pipe", 0, 1)')
        self.assertEqual(lua.eval("WORLD:sprite(1, 1, 0)"), "t_pipe_9_x9")

    def test_a_fence_on_an_edge_the_pipe_does_not_cross_draws_nothing(self):
        lua = world()
        edge(lua, 0, 0, True, "fence")
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 1, 0)')
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), "t_pipe_2")

    def test_a_shape_without_a_sleeve_keeps_its_plain_sprite(self):
        lua = world()
        edge(lua, 0, 1, True, "fence")
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 0, 1) place("Test:Pipe", 0, 2)')
        # mask 5 (N + S) has no sleeve in the test part
        self.assertEqual(lua.eval("WORLD:sprite(0, 1, 0)"), "t_pipe_5")


class Definition(unittest.TestCase):
    def lua(self):
        return new_lua("shared/LiveWater/LWT_API.lua")

    def test_sleeve_sprites_belong_to_the_part(self):
        lua = world()
        self.assertEqual(lua.eval('LiveWater.Parts:typeOfSprite("t_pipe_1_x1")'), "Test:Pipe")
        self.assertEqual(lua.eval('LiveWater.Parts:crossing("Test:Pipe", 9, 9)'), "t_pipe_9_x9")
        self.assertIsNone(lua.eval('LiveWater.Parts:crossing("Test:Pipe", 5, 1)'))

    def test_invalid_crossings_are_refused(self):
        for bad in ('{ [1] = { [8] = "x" } }', '{ [3] = { [2] = "x" } }', '{ [16] = { [1] = "x" } }',
                    '{ [1] = { [1] = 3 } }', '"x"'):
            lua = self.lua()
            ok = lua.eval('{ LiveWater.API.registerPart("T:Bad", { sprites = { [0] = "b" }, crossings = %s,'
                          ' capabilities = { conduit = true } }) }' % bad)
            self.assertEqual((ok[1], ok[2]), (False, "invalid_crossings"), bad)


class Relink(unittest.TestCase):
    def test_a_wall_set_down_later_splits_and_its_removal_joins_again(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 0, 1)')
        lua.execute("EMITTED = {}")
        edge(lua, 0, 1, True, "wall")
        lua.execute("TOPO:relink(0, 1, 0)")
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 0)
        self.assertNotEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(0, 1, 0)"))
        self.assertEqual(lua.eval("WORLD:sprite(0, 1, 0)"), "t_pipe_0")
        self.assertGreaterEqual(lua.eval('#emitted("networkChanged")'), 2)
        edge(lua, 0, 1, True, "fence")
        lua.execute("TOPO:relink(0, 1, 0)")
        self.assertEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(0, 1, 0)"))
        self.assertEqual(lua.eval("WORLD:sprite(0, 1, 0)"), "t_pipe_1_x1")

    def test_the_cut_is_kept_when_the_world_reloads_with_the_wall_unseen(self):
        lua = world()
        edge(lua, 0, 1, True, "wall")
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 0, 1)')
        self.assertEqual(lua.eval("REG:at(0, 1, 0).cuts"), 1)
        # new session on the same saved registry: far squares are not loaded, no edge is seen
        lua.execute("newServices(STORE) TOPO:rebuild()")
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 0)
        self.assertEqual(lua.eval("NET:mask(0, 1, 0)"), 0)

    def test_a_wall_built_without_an_event_is_found_by_the_clock_on_loaded_squares(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 0, 1) place("Test:Pipe", 5, 0) place("Test:Pipe", 5, 1)')
        edge(lua, 0, 1, True, "wall")
        edge(lua, 5, 1, True, "wall")
        lua.execute('WORLD.unloaded["5,1,0"] = true WORLD.unloaded["5,0,0"] = true EMITTED = {}')
        # both pipes along the wall changed: (0,0) on its S side, (0,1) on its N side
        self.assertEqual(lua.eval("TOPO:refreshCuts(function(x, y, z) return WORLD:isLoaded(x, y, z) end)"), 2)
        self.assertEqual(lua.eval("NET:mask(0, 0, 0)"), 0)
        self.assertEqual(lua.eval("NET:mask(5, 0, 0)"), 4)
        self.assertEqual(len(lua.eval("NET:ids()")), 3)
        self.assertEqual(lua.eval("TOPO:refreshCuts(function(x, y, z) return WORLD:isLoaded(x, y, z) end)"), 0)

    def test_a_square_without_parts_around_changes_nothing(self):
        lua = world()
        lua.execute('place("Test:Pipe", 5, 5)')
        lua.execute("EMITTED = {}")
        lua.execute("TOPO:relink(0, 0, 0)")
        self.assertEqual(lua.eval('#emitted("networkChanged")'), 0)



class PipeTiles(unittest.TestCase):
    def test_the_pipe_part_and_the_tile_recipe_agree_on_every_sleeve(self):
        import os
        import sys
        from lwt_harness import ROOT
        sys.path.insert(0, os.path.join(ROOT, "source", "tiles"))
        try:
            from build_livewater_tiles import crossings, tile_props
        finally:
            sys.path.pop(0)
        lua = new_lua("shared/LiveWater/LWT_API.lua", "shared/LiveWater/Parts/LWT_PartPipe.lua")
        listed = crossings()
        self.assertEqual(len(listed), 20)
        for mask, edges, index in listed:
            self.assertEqual(lua.eval('LiveWater.Parts:crossing("LiveWater:PipeGalvanized", %d, %d)' % (mask, edges)),
                             "batman_livewater_01_%d" % index)
            self.assertEqual(tile_props(index).get("CustomItem"), "Base.Mov_LiveWater_Pipe")

if __name__ == "__main__":
    unittest.main()
