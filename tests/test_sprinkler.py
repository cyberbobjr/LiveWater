"""E11: manual sprinkler (ADR-001 D19, P13, P14, D08a): part LiveWater:Sprinkler (outlet sprinkler, valve placed
closed, manual controller, spray), radius by definition times a sandbox multiplier, only the plants that need water,
200 ml doses really taken from the network, closed valve = nothing; valve command; the client jet (the only per-frame
subscription, D08a)."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
SPRINKLER = "shared/LiveWater/Parts/LWT_PartSprinkler.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class SprinklerPart(unittest.TestCase):
    def test_definition_follows_the_tile_contract_and_the_adr(self):
        lua = new_lua(API, SPRINKLER)
        d = lua.eval('LiveWater.API.part("LiveWater:Sprinkler")')
        for key, base in (("off", 48), ("on", 52)):
            self.assertEqual([d.variants[key][i] for i in range(1, 5)], [TILE + str(base + k) for k in range(4)], key)
        caps = d.capabilities
        self.assertEqual(caps.outlet.type, "sprinkler")
        self.assertFalse(caps.valve.open)
        self.assertEqual(caps.controller.mode, "manual")
        self.assertEqual((caps.spray.radius, caps.spray.dose), (2, 0.2))
        self.assertEqual((caps.spray.jetFirst, caps.spray.jetFrames), (80, 6))

    def test_the_look_follows_the_last_step(self):
        lua = new_lua(API, SPRINKLER)
        self.assertEqual(lua.eval('LiveWater.Parts:look({ type = "LiveWater:Sprinkler", data = {} })'), "off")
        self.assertEqual(lua.eval('LiveWater.Parts:look({ type = "LiveWater:Sprinkler",'
                                  ' data = { spray = { on = true } } })'), "on")

    def test_the_radius_is_scaled_by_the_sandbox_option(self):
        lua = new_lua(API, SPRINKLER)
        lua.execute('CTX = { scale = function(n) return n == "SprinklerRadiusMultiplier" and 2.5 or 1 end }'
                    ' PART = { type = "LiveWater:Sprinkler", data = {} }')
        self.assertEqual(call(lua, 'LiveWater.Parts:first(PART, "spray", CTX)'), (5, 0.2))
        self.assertEqual(call(lua, 'LiveWater.Parts:first(PART, "spray")'), (2, 0.2))

    def test_the_jet_hook_gives_the_frames_and_whether_it_sprays(self):
        lua = new_lua(API, SPRINKLER)
        t = lua.eval('{ LiveWater.Parts:first({ type = "LiveWater:Sprinkler", data = { spray = { on = true } } }, "jet") }')
        self.assertEqual((t[1], t[2], t[3], t[4]), (TILE, 80, 6, True))

    def test_api_revision_8_and_the_valve_hooks(self):
        lua = new_lua(API, SPRINKLER)
        self.assertGreaterEqual(lua.eval("LiveWater.API.revision"), 8)
        lua.execute('PART = { type = "LiveWater:Sprinkler", data = {} }')
        self.assertFalse(lua.eval('(LiveWater.Parts:first(PART, "opened"))'))
        self.assertTrue(lua.eval('LiveWater.Parts:any(PART, "blocks")'))
        lua.execute('LiveWater.Parts:call(PART, "open", true)')
        self.assertTrue(lua.eval('(LiveWater.Parts:first(PART, "opened"))'))
        self.assertFalse(lua.eval('LiveWater.Parts:any(PART, "blocks")'))
        actions = lua.eval('LiveWater.Parts:actions(PART)')
        self.assertEqual((actions[1].command, actions[1].key), ("switchValve", "ContextMenu_LWT_CloseValve"))


BENCH = r"""
FARM = { plants = {}, watered = {} }
function FARM:plant(x, y, z) return self.plants[x .. "," .. y] end
function FARM:water(x, y, z, doses)
    local p = self.plants[x .. "," .. y]
    if not p then return false end
    p.level = math.min(100, p.level + 10 * doses)
    self.watered[x .. "," .. y] = (self.watered[x .. "," .. y] or 0) + doses
    return true
end
function plant(x, y, level, needed, alive)
    FARM.plants[x .. "," .. y] = { alive = alive ~= false, level = level, needed = needed }
end
SCALE = {}
PLANTS = require("LiveWater/LWT_Plants").new({ catalog = LiveWater.Parts, farming = FARM,
    scale = function(n) return SCALE[n] end })
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
OUTLETS:register("sprinkler", PLANTS)
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, publisher = PUB,
    power = { powered = function() return true end },
    scale = function(n) return SCALE[n] end, need = function(part) return OUTLETS:need(part) end })
place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24")
place("Test:Pipe", 1, 0)
place("LiveWater:Sprinkler", 2, 0, "batman_livewater_01_48")
SPR = REG:at(2, 0, 0)
function delivered()
    EMITTED = {}
    CLOCK:tick()
    local d = emitted("waterDelivered")
    return d[1] and d[1][3] or 0
end
"""


def bench():
    lua = services(new_lua, POND, SPRINKLER)
    lua.execute(BENCH)
    return lua


class Watering(unittest.TestCase):
    def test_a_closed_valve_gives_nothing(self):
        lua = bench()
        lua.execute("plant(3, 0, 0, 70)")
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertEqual(lua.eval("FARM.plants['3,0'].level"), 0)
        self.assertEqual(lua.eval("SPR.data.outlet.state"), "closed")

    def test_open_it_waters_the_plants_that_need_it_by_200_ml_doses(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(SPR, "open", true)')
        lua.execute("plant(3, 0, 45, 70) plant(2, 1, 80, 70) plant(1, 1, 0, 70, false)")
        litres = lua.eval("delivered()")
        self.assertAlmostEqual(litres, 0.6)
        self.assertEqual(lua.eval("FARM.watered['3,0']"), 3)
        self.assertIsNone(lua.eval("FARM.watered['2,1']"))
        self.assertIsNone(lua.eval("FARM.watered['1,1']"))
        self.assertEqual(lua.eval("FARM.plants['3,0'].level"), 75)
        self.assertTrue(lua.eval("SPR.data.spray.on"))
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "52")

    def test_only_the_plants_in_the_radius(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(SPR, "open", true) plant(5, 0, 0, 10) plant(4, 1, 0, 10) plant(4, 0, 0, 10)')
        lua.execute("delivered()")
        self.assertIsNone(lua.eval("FARM.watered['5,0']"))
        self.assertIsNone(lua.eval("FARM.watered['4,1']"))
        self.assertEqual(lua.eval("FARM.watered['4,0']"), 1)
        lua.execute('SCALE.SprinklerRadiusMultiplier = 1.5 delivered()')
        self.assertEqual(lua.eval("FARM.watered['5,0']"), 1)

    def test_nothing_needed_is_idle_and_the_sprite_goes_off(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(SPR, "open", true) plant(3, 0, 0, 20)')
        lua.execute("delivered()")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "52")
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertEqual(lua.eval("SPR.data.outlet.state"), "idle")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "48")

    def test_short_water_gives_whole_doses_only(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(SPR, "open", true) plant(3, 0, 0, 100)')
        lua.execute("PLANTS:deliver(SPR, 0.5, 'tainted')")
        self.assertEqual(lua.eval("FARM.watered['3,0']"), 2)


COMMAND = r"""
SPRINKLE_EVENTS = {}
LiveWater.Events.on("valveChanged", function(part, open) table.insert(SPRINKLE_EVENTS, open) end)
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS,
    publisher = { present = function() end }, events = LiveWater.Events })
CMDS:register("switchValve", require("LiveWater/Commands/LWT_CmdSwitchValve"))
P = newPlayer(2, 1, 0)
place("LiveWater:Sprinkler", 2, 0, "batman_livewater_01_48")
place("Test:Pipe", 5, 5)
function cmd(x, y) return CMDS:dispatch(P, "switchValve", { x = x, y = y, z = 0 }) end
"""


class ValveCommand(unittest.TestCase):
    def bench(self):
        lua = services(new_lua, SPRINKLER)
        lua.execute(COMMAND)
        return lua

    def test_open_then_close_and_announce(self):
        lua = self.bench()
        self.assertTrue(lua.eval("cmd(2, 0)"))
        self.assertTrue(lua.eval("REG:at(2, 0, 0).data.valve.open"))
        self.assertTrue(lua.eval("cmd(2, 0)"))
        self.assertFalse(lua.eval("REG:at(2, 0, 0).data.valve.open"))
        self.assertEqual(list(lua.eval("SPRINKLE_EVENTS").values()), [True, False])

    def test_refusals(self):
        lua = self.bench()
        self.assertEqual(call(lua, "cmd(5, 5)"), (False, "not_valve"))
        self.assertEqual(call(lua, "cmd(9, 9)"), (False, "nothing_here"))
        lua.execute("P.x = 9")
        self.assertEqual(call(lua, "cmd(2, 0)"), (False, "too_far"))


JET = r"""
NOW = 0
function getTimestampMs() return NOW end
local function attached(obj)
    local list = obj.anims
    return { size = function() return #list end, get = function(_, i)
        local name = list[i + 1]
        return { getParentSprite = function() return { getName = function() return name end } end }
    end }
end
function newObject(sprite, state)
    local obj = { sprite = sprite, anims = {}, animating = false, state = state }
    obj.getSpriteName = function() return obj.sprite end
    obj.getModData = function() return { movableData = { LiveWater = obj.state } } end
    obj.getAttachedAnimSprite = function() return attached(obj) end
    obj.addAttachedAnimSpriteByName = function(_, name) table.insert(obj.anims, name) end
    obj.RemoveAttachedAnim = function(_, i) table.remove(obj.anims, i + 1) end
    obj.setAnimating = function(_, b) obj.animating = b end
    return obj
end
SQUARES = {}
function newSquare(x, y, objs)
    local sq = { getX = function() return x end, getY = function() return y end, getZ = function() return 0 end,
        getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
    SQUARES[x .. "," .. y] = sq
    return sq
end
function getCell() return { getGridSquare = function(_, x, y, z) return SQUARES[x .. "," .. y] end } end
function ticks() return #Events.OnTick.handlers end
function frame() fire("OnTick") end
"""


class Jet(unittest.TestCase):
    def bench(self, animated=True):
        lua = new_lua(API, SPRINKLER, "client/LiveWater/LWT_SprinklerJet.lua")
        lua.execute(JET)
        lua.execute("JET = require('LiveWater/LWT_SprinklerJet') JET.setAnimated(%s)" % ("true" if animated else "false"))
        lua.execute(r"""
        ON = { type = "LiveWater:Sprinkler", data = { spray = { on = true } } }
        OBJ = newObject("batman_livewater_01_53", ON)
        SQ = newSquare(4, 4, { OBJ })
        """)
        return lua

    def test_subscribes_once_while_a_running_sprinkler_is_loaded(self):
        lua = self.bench()
        self.assertEqual(lua.eval("ticks()"), 0)
        lua.execute('fire("LoadGridsquare", SQ) fire("LoadGridsquare", SQ)')
        self.assertEqual(lua.eval("ticks()"), 1)
        self.assertTrue(lua.eval("OBJ.animating"))
        self.assertEqual(list(lua.eval("OBJ.anims").values()), [TILE + "81"])

    def test_at_most_six_frames_per_second_facing_kept(self):
        lua = self.bench()
        lua.execute('fire("LoadGridsquare", SQ)')
        lua.execute("NOW = 100 frame()")
        self.assertEqual(list(lua.eval("OBJ.anims").values()), [TILE + "81"])
        lua.execute("NOW = 170 frame()")
        self.assertEqual(list(lua.eval("OBJ.anims").values()), [TILE + "85"])
        lua.execute("for i = 1, 60 do NOW = NOW + 1000 / 60 frame() end")
        self.assertEqual(lua.eval("JET.swaps"), 6)

    def test_stops_and_unsubscribes_when_no_running_sprinkler_remains(self):
        lua = self.bench()
        lua.execute('fire("LoadGridsquare", SQ)')
        lua.execute('OBJ.state = { type = "LiveWater:Sprinkler", data = { spray = { on = false } } }'
                    ' fire("OnServerCommand", "LiveWater", "jet", { x = 4, y = 4, z = 0 })')
        self.assertEqual(lua.eval("ticks()"), 0)
        self.assertFalse(lua.eval("OBJ.animating"))
        self.assertEqual(len(lua.eval("OBJ.anims")), 0)

    def test_an_unloaded_square_leaves(self):
        lua = self.bench()
        lua.execute('fire("LoadGridsquare", SQ) fire("ReuseGridsquare", SQ)')
        self.assertEqual(lua.eval("ticks()"), 0)

    def test_the_loop_reattaches_after_a_sprite_update_cleared_it(self):
        lua = self.bench()
        lua.execute('fire("LoadGridsquare", SQ) OBJ.anims = {} NOW = 500 frame()')
        self.assertEqual(len(lua.eval("OBJ.anims")), 1)

    def test_still_jet_option_attaches_one_frame_without_tick(self):
        lua = self.bench(animated=False)
        lua.execute('fire("LoadGridsquare", SQ)')
        self.assertEqual(lua.eval("ticks()"), 0)
        self.assertEqual(list(lua.eval("OBJ.anims").values()), [TILE + "81"])

    def test_a_placed_running_sprinkler_is_seen(self):
        lua = self.bench()
        lua.execute('OBJ.getSquare = function() return SQ end fire("OnObjectAdded", OBJ)')
        self.assertEqual(lua.eval("ticks()"), 1)


class Texts(unittest.TestCase):
    def test_scripts_sandbox_and_translations(self):
        with open(os.path.join(MEDIA, "scripts", "LWT_moveables.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"item Mov_LiveWater_Sprinkler\s*\{[^}]*WorldObjectSprite = batman_livewater_01_48,")
        with open(os.path.join(MEDIA, "scripts", "LWT_recipes.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"(?s)craftRecipe LWTBuildSprinkler\s*\{.*?item 1 Base\.Mov_LiveWater_Sprinkler,")
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"option LiveWater\.SprinklerRadiusMultiplier\s*\{\s*type = double,[^}]*default = 1\.0,")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            self.assertIn("ContextMenu_LWT_OpenValve", load("ContextMenu.json"), lang)
            self.assertIn("IGUI_LWT_Valve_Closed", load("IG_UI.json"), lang)
            self.assertIn("Sandbox_LWT_SprinklerRadiusMultiplier", load("Sandbox.json"), lang)
            self.assertIn("LWTBuildSprinkler", load("Recipes.json"), lang)
            self.assertIn("UI_LWT_AnimatedJet", load("UI.json"), lang)


if __name__ == "__main__":
    unittest.main()
