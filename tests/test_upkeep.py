"""E15: pump upkeep (ADR-001 D24, P03-P05, P08, P15, Q05): on/off switch besides the auto-stop, efficiency lost per
running minute with a flow in proportion, random breakdowns below 20 %, stop at 0 % (no fire), repair when stopped
with scrap metal, information lines in the part menu, a pump sound loop heard by players and noise for zombies."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"

BENCH = r"""
POWER = { powered = function() return true end }
NEED = {}
SOUNDS = { log = {} }
function SOUNDS:loop(x, y, z, name) table.insert(self.log, { "loop", x, y, name or false }) end
function SOUNDS:noise(x, y, z, radius, volume) table.insert(self.log, { "noise", x, y, radius, volume }) end
function soundLog(kind) local n = 0 for _, e in ipairs(SOUNDS.log) do if e[1] == kind then n = n + 1 end end return n end
RANDOM = 0.99
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD, sounds = SOUNDS })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, power = POWER, publisher = PUB,
    random = function() return RANDOM end,
    need = function(part) return NEED[part.x .. "," .. part.y] or 0 end })
Commands = require("LiveWater/LWT_Commands")
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS, publisher = PUB })
CMDS:register("switchPump", require("LiveWater/Commands/LWT_CmdSwitchPump"))
CMDS:register("repairPump", require("LiveWater/Commands/LWT_CmdRepairPump"))
P = newPlayer(0, 1, 0, { ["Base.ScrapMetal"] = 3 }, { ["base:wrench"] = true })
function cmd(name, args) args = args or {} args.x, args.y, args.z = 0, 0, 0 return CMDS:dispatch(P, name, args) end
place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:Spr", 1, 0)
PUMP = REG:at(0, 0, 0)
PUMP.data.pump = {}
function delivered()
    EMITTED = {}
    CLOCK:tick()
    local d = emitted("waterDelivered")
    return d[1] and d[1][3] or 0
end
"""


def bench():
    lua = services(new_lua, POND)
    lua.execute(BENCH)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Switch(unittest.TestCase):
    def test_a_pump_switched_off_gives_nothing_until_switched_on(self):
        lua = bench()
        lua.execute('NEED["1,0"] = 100')
        self.assertEqual(lua.eval("delivered()"), 50)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "28")
        self.assertTrue(lua.eval('cmd("switchPump")'))
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "24")
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertEqual(lua.eval("LiveWater.Parts:lines(PUMP)[1][1]"), "IGUI_LWT_Pump_Off")
        lua.execute('cmd("switchPump")')
        self.assertAlmostEqual(lua.eval("delivered()"), 50, delta=0.1)

    def test_switch_refused_far_away(self):
        lua = bench()
        lua.execute("P.x = 9")
        self.assertEqual(call(lua, 'cmd("switchPump")'), (False, "too_far"))


class Wear(unittest.TestCase):
    def test_efficiency_drops_per_running_minute_and_the_flow_follows(self):
        lua = bench()
        lua.execute('NEED["1,0"] = 100 delivered()')
        self.assertAlmostEqual(lua.eval("PUMP.data.pump.efficiency"), 99.9)
        lua.execute("PUMP.data.pump.efficiency = 50")
        self.assertEqual(lua.eval("delivered()"), 25)

    def test_no_wear_while_stopped(self):
        lua = bench()
        lua.execute("delivered()")
        self.assertIsNone(lua.eval("PUMP.data.pump.efficiency"))

    def test_the_sandbox_multiplier_scales_the_wear(self):
        lua = bench()
        lua.execute('CLOCK.ctx.scale = function(n) return n == "PumpWearMultiplier" and 3 or 1 end NEED["1,0"] = 5 delivered()')
        self.assertAlmostEqual(lua.eval("PUMP.data.pump.efficiency"), 99.7)

    def test_random_breakdowns_only_below_20_percent(self):
        lua = bench()
        lua.execute('RANDOM = 0 NEED["1,0"] = 5 PUMP.data.pump.efficiency = 30 delivered()')
        self.assertFalse(lua.eval("PUMP.data.pump.broken == true"))
        lua.execute("PUMP.data.pump.efficiency = 15 delivered()")
        self.assertTrue(lua.eval("PUMP.data.pump.broken"))
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertEqual(lua.eval("LiveWater.Parts:lines(PUMP)[1][1]"), "IGUI_LWT_Pump_Broken")

    def test_no_breakdown_when_the_dice_say_no_and_stop_at_zero(self):
        lua = bench()
        lua.execute('RANDOM = 0.99 NEED["1,0"] = 5 PUMP.data.pump.efficiency = 15 delivered()')
        self.assertFalse(lua.eval("PUMP.data.pump.broken == true"))
        lua.execute("PUMP.data.pump.efficiency = 0.05 delivered()")
        self.assertEqual(lua.eval("PUMP.data.pump.efficiency"), 0)
        self.assertTrue(lua.eval("PUMP.data.pump.broken"))


class Repair(unittest.TestCase):
    def test_repair_of_a_stopped_pump_with_scrap_metal(self):
        lua = bench()
        lua.execute("PUMP.data.pump.efficiency = 0 PUMP.data.pump.broken = true")
        self.assertTrue(lua.eval('cmd("repairPump")'))
        self.assertEqual(lua.eval('P.items["Base.ScrapMetal"]'), 1)
        self.assertEqual(lua.eval("PUMP.data.pump.efficiency"), 100)
        self.assertFalse(lua.eval("PUMP.data.pump.broken"))

    def test_refusals(self):
        lua = bench()
        self.assertEqual(call(lua, 'cmd("repairPump")'), (False, "not_needed"))
        lua.execute('PUMP.data.pump.efficiency = 60 NEED["1,0"] = 5 delivered()')
        self.assertEqual(call(lua, 'cmd("repairPump")'), (False, "running"))
        lua.execute('NEED["1,0"] = 0 delivered() P.tools = {}')
        self.assertEqual(call(lua, 'cmd("repairPump")'), (False, "need_wrench"))
        lua.execute('P.tools = { ["base:wrench"] = true } P.items["Base.ScrapMetal"] = 1')
        self.assertEqual(call(lua, 'cmd("repairPump")'), (False, "no_parts"))
        self.assertEqual(lua.eval("P.told[#P.told]"), "IGUI_LWT_NoScrap")


class Sound(unittest.TestCase):
    def test_the_loop_starts_and_stops_with_the_pump_and_zombies_hear_it_each_step(self):
        lua = bench()
        lua.execute('NEED["1,0"] = 5 SOUNDS.log = {} delivered()')
        self.assertEqual(lua.eval('soundLog("noise")'), 1)
        self.assertEqual(lua.eval("SOUNDS.log[#SOUNDS.log][4]"), "GeneratorLoop")
        lua.execute('NEED["1,0"] = 0 SOUNDS.log = {} delivered()')
        self.assertEqual(lua.eval('soundLog("noise")'), 0)
        self.assertEqual(lua.eval("SOUNDS.log[1][4]"), False)
        lua.execute("SOUNDS.log = {} delivered()")
        self.assertEqual(lua.eval("#SOUNDS.log"), 0)

    def test_the_client_plays_one_loop_per_pump_and_stops_it(self):
        lua = new_lua("shared/LiveWater/LWT_API.lua", "client/LiveWater/LWT_PumpSounds.lua")
        lua.execute(r"""
        STARTED, STOPPED = 0, 0
        local emitter = { playSoundImpl = function(_, name, world, parent) STARTED = STARTED + 1 return STARTED end,
            stopSound = function(_, id) STOPPED = STOPPED + 1 end, isPlaying = function() return true end }
        function getWorld() return { getFreeEmitter = function() return emitter end } end
        function send(name) fire("OnServerCommand", "LiveWater", "sound", { x = 1, y = 2, z = 0, name = name }) end
        """)
        lua.execute('send("GeneratorLoop") send("GeneratorLoop")')
        self.assertEqual(lua.eval("STARTED"), 1)
        lua.execute("send(nil)")
        self.assertEqual(lua.eval("STOPPED"), 1)
        lua.execute('fire("OnServerCommand", "Other", "sound", { x = 1, y = 2, z = 0, name = "X" })')
        self.assertEqual(lua.eval("STARTED"), 1)


MENU = r"""
SENT = {}
function sendClientCommand(player, module, command, args) table.insert(SENT, { module, command, args }) end
function getText(key, a) if a ~= nil then return key .. "|" .. tostring(a) end return key end
ISToolTip = { new = function() return { initialise = function() end, setName = function() end } end }
STATE = nil
local function object(sprite)
    return { getSpriteName = function() return sprite end,
             getModData = function() return { movableData = { LiveWater = STATE } } end }
end
function getSpecificPlayer(n) return MENU_PLAYER end
function click(sprites, items)
    MENU_PLAYER = { getInventory = function() return { containsTypeRecurse = function(_, t) return items[t] == true end } end }
    local objs = {}
    for i, s in ipairs(sprites) do objs[i] = object(s) end
    local sq = { getX = function() return 4 end, getY = function() return 5 end, getZ = function() return 0 end,
        getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
    OPTIONS = {}
    local context = { addOption = function(self, text, target, fn, ...)
        local o = { text = text } table.insert(OPTIONS, o) return o end,
        addSubMenu = function(self, option, sub) option.sub = sub end }
    fire("OnFillWorldObjectContextMenu", 0, context, { { getSquare = function() return sq end } }, false)
end
function texts() local out = {} for i, o in ipairs(OPTIONS) do out[i] = o.text end return out end
"""


class Menu(unittest.TestCase):
    def menu(self, state):
        lua = new_lua("shared/LiveWater/LWT_API.lua", POND, "client/LiveWater/LWT_PartMenu.lua")
        lua.execute(MENU)
        lua.execute('STATE = { type = "LiveWater:PondPump", data = %s }' % state)
        return lua

    def test_switch_and_information(self):
        lua = self.menu("{ pump = { running = true, litres = 50 }, intake = { source = 'water' } }")
        lua.execute('click({ "%s28" }, {})' % TILE)
        texts = list(lua.eval("texts()").values())
        self.assertIn("ContextMenu_LWT_TurnOff", texts)
        self.assertIn("ContextMenu_LWT_Info", texts)
        self.assertNotIn("ContextMenu_LWT_Repair", texts)
        info = [o for o in lua.eval("OPTIONS").values() if o.text == "ContextMenu_LWT_Info"][0]
        self.assertIn("IGUI_LWT_Pump_Running", info.toolTip.description)
        self.assertIn("IGUI_LWT_Pump_Flow|50", info.toolTip.description)
        self.assertIn("IGUI_LWT_Source_water", info.toolTip.description)

    def test_repair_offered_on_a_stopped_worn_pump_with_scrap(self):
        lua = self.menu("{ pump = { on = false, efficiency = 40 } }")
        lua.execute('click({ "%s24" }, { ["Base.ScrapMetal"] = true })' % TILE)
        texts = list(lua.eval("texts()").values())
        self.assertIn("ContextMenu_LWT_TurnOn", texts)
        self.assertIn("ContextMenu_LWT_Repair", texts)


class Texts(unittest.TestCase):
    def test_sandbox_option_and_translations(self):
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"option LiveWater\.PumpWearMultiplier\s*\{\s*type = double, min = 0\.0,"
                                       r" max = [\d.]+, default = 1\.0,")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            ui, menu = load("IG_UI.json"), load("ContextMenu.json")
            for key in ("IGUI_LWT_Pump_Off", "IGUI_LWT_Pump_Broken", "IGUI_LWT_Pump_Efficiency", "IGUI_LWT_Source_water",
                        "IGUI_LWT_NoScrap", "IGUI_LWT_NotNeeded", "IGUI_LWT_StillRunning", "IGUI_LWT_NeedWrench"):
                self.assertIn(key, ui, lang)
            for key in ("ContextMenu_LWT_TurnOn", "ContextMenu_LWT_TurnOff", "ContextMenu_LWT_Repair",
                        "ContextMenu_LWT_Info"):
                self.assertIn(key, menu, lang)
            self.assertIn("Sandbox_LWT_PumpWearMultiplier", load("Sandbox.json"), lang)


if __name__ == "__main__":
    unittest.main()
