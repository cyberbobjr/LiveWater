"""E07: placement and removal on the authority (ADR-001 D03, D06, D10): a part tile recognised by its sprite
through the part catalog joins the registry and the network graph (merge, split), events are emitted, the
graph is rebuilt from the registry at load; the server composition root wires the game events."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua


def world():
    lua = services(new_lua)
    lua.execute('PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function(m) table.insert(LOGS, m) end)')
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Added(unittest.TestCase):
    def test_a_part_sprite_joins_the_registry_and_the_network(self):
        lua = world()
        lua.execute('WORLD:createPart(3, 4, 0, "t_pipe_0") OK = PLACEMENT:added("t_pipe_0", 3, 4, 0)')
        self.assertTrue(lua.eval("OK"))
        self.assertEqual(lua.eval("REG:at(3, 4, 0).type"), "Test:Pipe")
        self.assertTrue(lua.eval("NET:part(3, 4, 0) == REG:at(3, 4, 0)"))
        self.assertEqual(len(lua.eval('emitted("partAdded")')), 1)
        self.assertEqual(len(lua.eval('emitted("networkChanged")')), 1)

    def test_any_sprite_of_the_type_identifies_it(self):
        lua = world()
        self.assertTrue(lua.eval('PLACEMENT:added("t_pipe_9", 0, 0, 0)'))
        self.assertEqual(lua.eval("REG:at(0, 0, 0).type"), "Test:Pipe")

    def test_an_unrelated_sprite_is_ignored(self):
        lua = world()
        self.assertEqual(call(lua, 'PLACEMENT:added("crafted_01_0", 0, 0, 0)'), (False, "not_a_part"))
        self.assertIsNone(lua.eval("REG:at(0, 0, 0)"))
        self.assertEqual(len(lua.eval('emitted("partAdded")')), 0)

    def test_the_same_part_seen_twice_is_added_once(self):
        lua = world()
        lua.execute('PLACEMENT:added("t_pipe_0", 0, 0, 0)')
        self.assertTrue(lua.eval('PLACEMENT:added("t_pipe_0", 0, 0, 0)'))
        self.assertEqual(len(lua.eval('emitted("partAdded")')), 1)

    def test_a_refused_part_is_reported_and_logged(self):
        lua = services(new_lua, pump_ports=1)
        lua.execute('PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function(m) table.insert(LOGS, m) end)')
        lua.execute('place("Test:Pump", 0, 0) place("Test:Pipe", 1, 0)')
        self.assertEqual(call(lua, 'PLACEMENT:added("t_pipe_0", -1, 0, 0)'), (False, "ports_full"))
        self.assertIsNone(lua.eval("REG:at(-1, 0, 0)"))
        self.assertIn("ports_full", lua.eval("LOGS[#LOGS]"))

    def test_merge_of_two_networks(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 2, 0)')
        self.assertNotEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(2, 0, 0)"))
        lua.execute('PLACEMENT:added("t_pipe_0", 1, 0, 0)')
        self.assertEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(2, 0, 0)"))


class Removed(unittest.TestCase):
    def test_removal_splits_the_network_and_is_announced(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0) place("Test:Pipe", 1, 0) place("Test:Pipe", 2, 0)')
        lua.execute('EMITTED = {} OK = PLACEMENT:removed("t_pipe_10", 1, 0, 0)')
        self.assertTrue(lua.eval("OK"))
        self.assertIsNone(lua.eval("REG:at(1, 0, 0)"))
        self.assertIsNone(lua.eval("NET:part(1, 0, 0)"))
        self.assertNotEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(2, 0, 0)"))
        removed = lua.eval('emitted("partRemoved")')
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[1][2].x, 1)
        self.assertEqual(len(lua.eval('emitted("networkChanged")')), 2)

    def test_another_object_of_the_square_leaves_the_part(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0)')
        self.assertEqual(call(lua, 'PLACEMENT:removed("t_pump", 0, 0, 0)'), (False, "not_a_part"))
        self.assertEqual(call(lua, 'PLACEMENT:removed("crafted_01_0", 0, 0, 0)'), (False, "not_a_part"))
        self.assertEqual(lua.eval("REG:at(0, 0, 0).type"), "Test:Pipe")

    def test_removing_twice_is_harmless(self):
        lua = world()
        lua.execute('place("Test:Pipe", 0, 0) PLACEMENT:removed("t_pipe_0", 0, 0, 0)')
        self.assertEqual(call(lua, 'PLACEMENT:removed("t_pipe_0", 0, 0, 0)'), (False, "not_a_part"))


class Rebuild(unittest.TestCase):
    def test_graph_rebuilt_from_the_registry_in_placement_order(self):
        lua = world()
        lua.execute("""
        newServices({ seq = 3, parts = {
            ["0,0,0"] = { v = 1, type = "Test:Pump", x = 0, y = 0, z = 0, order = 1, data = {} },
            ["1,0,0"] = { v = 1, type = "Test:Pipe", x = 1, y = 0, z = 0, order = 2, data = {} },
            ["2,0,0"] = { v = 1, type = "Gone:Pipe", x = 2, y = 0, z = 0, order = 3, data = {} } } })
        COUNT = TOPO:rebuild()
        """)
        self.assertEqual(lua.eval("COUNT"), 2)
        self.assertEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(1, 0, 0)"))
        self.assertIsNone(lua.eval("NET:part(2, 0, 0)"))
        self.assertEqual(lua.eval("REG:at(2, 0, 0).type"), "Gone:Pipe")
        self.assertEqual(lua.eval("NET:part(1, 0, 0).order"), 2)
        self.assertEqual(len(lua.eval('emitted("partAdded")')), 0)


class PipePart(unittest.TestCase):
    def test_galvanized_pipe_follows_the_tile_contract(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", "shared/LiveWater/Parts/LWT_PartPipe.lua")
        d = lua.eval('LiveWater.API.part("LiveWater:PipeGalvanized")')
        self.assertEqual([d.sprites[m] for m in range(16)], ["batman_livewater_01_%d" % m for m in range(16)])
        self.assertEqual(d.sides, 15)
        self.assertIsNotNone(d.capabilities.conduit)
        self.assertEqual(d.capabilities.layable.item, "LiveWater.PipeSection")
        self.assertEqual(d.capabilities.layable.tool, "base:pipewrench")


GAME = r"""
LOADED_SQUARES = {}
local function fakeObject(sprite, sq)
    local o = { sprite = sprite, sq = sq }
    function o:getSpriteName() return self.sprite end
    function o:getSquare() return self.sq end
    function o:setSpriteFromName(n) self.sprite = n end
    function o:transmitUpdatedSpriteToClients() self.sent = (self.sent or 0) + 1 end
    function o:getModData() self.md = self.md or {} return self.md end
    function o:hasModData() return self.md ~= nil end
    function o:transmitModData() end
    function o:getSprite() return self.spriteObj end
    function o:getFluidContainer() return self.fc end
    return o
end
function instanceof() return false end
IsoFlagType = { waterPiped = "waterPiped" }
-- A water fixture: its sprite carries the waterPiped flag.
function addFixture(x, y, z)
    local o = addObject("fixtures_sinks_01_0", x, y, z)
    o.spriteObj = { getProperties = function() return { has = function(_, f) return f == "waterPiped" end } end }
    return o
end
function fakeSquare(x, y, z)
    local sq = { x = x, y = y, z = z, objs = {} }
    function sq:getX() return self.x end
    function sq:getY() return self.y end
    function sq:getZ() return self.z end
    function sq:getObjects()
        local list = self.objs
        return { size = function() return #list end, get = function(_, i) return list[i + 1] end }
    end
    LOADED_SQUARES[x .. "," .. y .. "," .. z] = sq
    return sq
end
function addObject(sprite, x, y, z)
    local sq = LOADED_SQUARES[x .. "," .. y .. "," .. z] or fakeSquare(x, y, z)
    local o = fakeObject(sprite, sq)
    table.insert(sq.objs, o)
    return o
end
CELL = { getGridSquare = function(self, x, y, z) return LOADED_SQUARES[x .. "," .. y .. "," .. z] end }
function getCell() return CELL end
GLOBAL_MODDATA = {}
ModData = { getOrCreate = function(name)
    GLOBAL_MODDATA[name] = GLOBAL_MODDATA[name] or {}
    return GLOBAL_MODDATA[name]
end }
function isServer() return false end
function getGameTime() return { getWorldAgeHours = function() return 0 end } end
"""


class Wiring(unittest.TestCase):
    def server(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", "shared/LiveWater/Parts/LWT_PartPipe.lua")
        lua.execute(GAME)
        lua.execute('SERVER = require("LiveWater/LWT_Server")')
        return lua

    def test_init_reads_the_global_moddata_and_rebuilds(self):
        lua = self.server()
        lua.execute("""
        GLOBAL_MODDATA.LiveWater = { seq = 1, parts = { ["5,5,0"] = { v = 1, type = "LiveWater:PipeGalvanized",
            x = 5, y = 5, z = 0, order = 1, data = {} } } }
        fire("OnInitGlobalModData", false)
        """)
        self.assertEqual(lua.eval('LiveWater.Server.topology:at(5, 5, 0).type'), "LiveWater:PipeGalvanized")
        self.assertIsNotNone(lua.eval("LiveWater.Server.network:networkAt(5, 5, 0)"))

    def test_object_added_and_removed_events_drive_the_registry_and_sprites(self):
        lua = self.server()
        lua.execute("""
        fire("OnInitGlobalModData", true)
        A = addObject("batman_livewater_01_0", 0, 0, 0)
        fire("OnObjectAdded", A)
        B = addObject("batman_livewater_01_0", 1, 0, 0)
        fire("OnObjectAdded", B)
        """)
        self.assertEqual(lua.eval("GLOBAL_MODDATA.LiveWater.parts['0,0,0'].type"), "LiveWater:PipeGalvanized")
        self.assertEqual(lua.eval("A.sprite"), "batman_livewater_01_2")
        self.assertEqual(lua.eval("B.sprite"), "batman_livewater_01_8")
        self.assertEqual(lua.eval("A.sent"), 1)
        lua.execute('fire("OnObjectAboutToBeRemoved", B)')
        self.assertIsNone(lua.eval("GLOBAL_MODDATA.LiveWater.parts['1,0,0']"))
        self.assertEqual(lua.eval("A.sprite"), "batman_livewater_01_0")

    def test_fixtures_set_down_or_taken_and_chunks_loaded_reach_the_relays(self):
        lua = self.server()
        lua.execute("""
        fire("OnInitGlobalModData", true)
        TOUCHED, CHUNKS = {}, {}
        LiveWater.Server.relays.touched = function(_, x, y) table.insert(TOUCHED, x .. "," .. y) end
        LiveWater.Server.relays.chunkLoaded = function(_, x, y, n) table.insert(CHUNKS, x .. "," .. y .. "," .. n) end
        F = addFixture(3, 4, 0)
        fire("OnObjectAdded", F)
        fire("OnObjectAdded", addObject("batman_livewater_01_0", 9, 9, 0))
        fire("OnObjectAboutToBeRemoved", F)
        fire("LoadChunk", { getGridSquare = function(_, x, y, z) return fakeSquare(16 + x, 24 + y, z) end })
        """)
        self.assertEqual(list(lua.eval("TOUCHED").values()), ["3,4", "3,4"])
        self.assertEqual(list(lua.eval("CHUNKS").values()), ["16,24,8"])

    def test_events_before_init_are_ignored(self):
        lua = self.server()
        lua.execute('fire("OnObjectAdded", addObject("batman_livewater_01_0", 0, 0, 0)) fire("EveryTenMinutes")')
        self.assertIsNone(lua.eval("GLOBAL_MODDATA.LiveWater"))


if __name__ == "__main__":
    unittest.main()
