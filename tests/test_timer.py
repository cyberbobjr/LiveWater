"""E12: automatic sprinkler (ADR-001 D19, D20): recipe LWTUpgradeSprinkler (Electrical 2) turns the manual sprinkler
into LiveWater:SprinklerAuto; its timer opens it once per slice of X hours (slice number compared, not the minute),
for 30 minutes (three ten-minute steps, controller setting `duration`, ADR-006 D03), drawing its flow; the timer is an electric consumer (a few W, through LWT_Power): no current, no
trigger; opening it by hand stays possible; the interval is set on the sprinkler within sandbox bounds."""
import json
import os
import re
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
from test_sprinkler import BENCH as SPRINKLER_BENCH

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
SPRINKLER = "shared/LiveWater/Parts/LWT_PartSprinkler.lua"
AUTO = "shared/LiveWater/Parts/LWT_PartSprinklerAuto.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class AutoPart(unittest.TestCase):
    def test_definition_follows_the_tile_contract_and_the_adr(self):
        lua = new_lua(API, SPRINKLER, AUTO)
        d = lua.eval('LiveWater.API.part("LiveWater:SprinklerAuto")')
        for key, base in (("off", 56), ("on", 60)):
            self.assertEqual([d.variants[key][i] for i in range(1, 5)], [TILE + str(base + k) for k in range(4)], key)
        caps = d.capabilities
        self.assertEqual((caps.controller.mode, caps.controller.every, caps.controller.watts), ("timer", 6, 5))
        self.assertEqual(caps.controller.duration, 3)
        self.assertEqual(caps.outlet.type, "sprinkler")
        self.assertFalse(caps.valve.open)
        self.assertEqual(caps.spray.radius, 2)
        self.assertGreaterEqual(lua.eval("LiveWater.API.revision"), 9)

    def test_the_timer_needs_a_few_watts_the_manual_one_none(self):
        lua = new_lua(API, SPRINKLER, AUTO)
        t = lua.eval('{ LiveWater.Parts:first({ type = "LiveWater:SprinklerAuto", data = {} }, "power") }')
        self.assertEqual((t[1], t[2]), (True, 5))
        self.assertIsNone(lua.eval('(LiveWater.Parts:first({ type = "LiveWater:Sprinkler", data = {} }, "power"))'))


TIMER = r"""
HOURS = 0
CLOCK.hours = function() return HOURS end
POWERED = true
CLOCK.power = { powered = function(self, part) return part.type ~= "LiveWater:SprinklerAuto" or POWERED end }
TOPO:remove(2, 0, 0) WORLD:removePart(2, 0, 0, "LiveWater:Sprinkler")
place("LiveWater:SprinklerAuto", 2, 0, "batman_livewater_01_57")
SPR = REG:at(2, 0, 0)
"""


def bench():
    lua = services(new_lua, POND, SPRINKLER, AUTO)
    lua.execute(SPRINKLER_BENCH)
    lua.execute(TIMER)
    return lua


class Timer(unittest.TestCase):
    def test_once_per_slice_for_thirty_minutes(self):
        # ADR-006 D03: three steps of its flow (10 L each), thirsty plants or not, then closed until the next slice
        lua = bench()
        lua.execute("plant(3, 0, 40, 70)")
        self.assertAlmostEqual(lua.eval("delivered()"), 10)
        self.assertEqual(lua.eval("FARM.watered['3,0']"), 3)
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "63")   # on, turned W to its pipe
        self.assertTrue(lua.eval("SPR.data.controller.watering"))
        self.assertAlmostEqual(lua.eval("delivered()"), 10)
        self.assertEqual(lua.eval("SPR.data.outlet.state"), "served")
        self.assertAlmostEqual(lua.eval("delivered()"), 10)
        self.assertFalse(lua.eval("SPR.data.controller.watering"))
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertEqual(lua.eval("SPR.data.outlet.state"), "closed")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "59")   # off, turned W
        lua.execute("HOURS = 5.9")
        self.assertEqual(lua.eval("delivered()"), 0)
        lua.execute("HOURS = 6")
        self.assertAlmostEqual(lua.eval("delivered()"), 10)

    def test_the_duration_is_a_controller_setting(self):
        lua = new_lua(API)
        lua.execute('LiveWater.API.registerPart("T:Auto", { sprites = { [0] = "ta" }, capabilities = {'
                    ' valve = { open = false }, controller = { mode = "timer", duration = 1 } } })'
                    ' PART = { type = "T:Auto", data = {} }'
                    ' LiveWater.Parts:call(PART, "prepare", { hours = 0 })')
        self.assertFalse(lua.eval("LiveWater.Parts:closed(PART)"))
        lua.execute('LiveWater.Parts:call(PART, "stepped", { outlet = "served" })')
        self.assertTrue(lua.eval("LiveWater.Parts:closed(PART)"))
        self.assertFalse(lua.eval('(LiveWater.API.registerPart("T:Bad", { sprites = { [0] = "tb" },'
                                  ' capabilities = { controller = { mode = "timer", duration = 0 } } }))'))

    def test_the_thirty_minutes_run_even_when_the_water_is_short(self):
        # the timer counts steps, not water: a dry step still uses one of its three
        lua = bench()
        lua.execute("REG:at(0, 0, 0).data.pump = { on = false } delivered() delivered()")
        lua.execute("REG:at(0, 0, 0).data.pump.on = true")
        self.assertAlmostEqual(lua.eval("delivered()"), 10)
        self.assertEqual(lua.eval("delivered()"), 0)

    def test_the_interval_set_on_the_sprinkler_is_used(self):
        lua = bench()
        lua.execute('LiveWater.Parts:call(SPR, "setTimer", 2) delivered() delivered() delivered()')
        self.assertEqual(lua.eval("delivered()"), 0)
        lua.execute("HOURS = 2")
        self.assertAlmostEqual(lua.eval("delivered()"), 10)
        self.assertEqual(lua.eval('(LiveWater.Parts:first(SPR, "timer"))'), 2)

    def test_no_current_no_trigger(self):
        lua = bench()
        lua.execute("plant(3, 0, 40, 70) POWERED = false")
        self.assertEqual(lua.eval("delivered()"), 0)
        self.assertEqual(lua.eval("SPR.data.outlet.state"), "closed")
        lines = [l[1] for l in lua.eval("LiveWater.Parts:lines(SPR)").values()]
        self.assertIn("IGUI_LWT_Timer_NoPower", lines)

    def test_opening_by_hand_stays_possible_without_current(self):
        lua = bench()
        lua.execute('plant(3, 0, 40, 70) POWERED = false LiveWater.Parts:call(SPR, "open", true)')
        self.assertAlmostEqual(lua.eval("delivered()"), 10)  # its flow (ADR-006 D01)


COMMAND = r"""
Commands = require("LiveWater/LWT_Commands")
BOUNDS = { SprinklerTimerMin = 2, SprinklerTimerMax = 12 }
CMDS = Commands.new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS,
    publisher = { present = function() end }, events = LiveWater.Events, scale = function(n) return BOUNDS[n] end })
CMDS:register("setTimer", require("LiveWater/Commands/LWT_CmdSetTimer"))
P = newPlayer(2, 1, 0)
place("LiveWater:SprinklerAuto", 2, 0, "batman_livewater_01_56")
place("LiveWater:Sprinkler", 4, 0, "batman_livewater_01_48")
function cmd(x, hours) return CMDS:dispatch(P, "setTimer", { x = x, y = 0, z = 0, hours = hours }) end
"""


class SetTimer(unittest.TestCase):
    def bench(self):
        lua = services(new_lua, SPRINKLER, AUTO)
        lua.execute(COMMAND)
        return lua

    def test_set_within_the_sandbox_bounds(self):
        lua = self.bench()
        self.assertTrue(lua.eval("cmd(2, 3)"))
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.controller.every"), 3)
        self.assertEqual(call(lua, "cmd(2, 1)"), (False, "out_of_bounds"))
        self.assertEqual(call(lua, "cmd(2, 24)"), (False, "out_of_bounds"))
        self.assertEqual(call(lua, "cmd(2, 2.5)"), (False, "invalid"))
        self.assertEqual(call(lua, "cmd(4, 3)"), (False, "not_timer"))

    def test_the_menu_offers_the_choices_of_the_timer(self):
        lua = new_lua(API, SPRINKLER, AUTO)
        actions = lua.eval('LiveWater.Parts:actions({ type = "LiveWater:SprinklerAuto", data = {} })')
        timer = [a for a in actions.values() if a.command == "setTimer"][0]
        hours = [c.args.hours for c in timer.choices.values()]
        self.assertIn(6, hours)
        self.assertEqual(timer.choices[1].key, "ContextMenu_LWT_EveryHours")


class TimerMenu(unittest.TestCase):
    def test_the_hours_are_a_submenu_that_sends_them(self):
        from test_upkeep import MENU
        lua = new_lua(API, SPRINKLER, AUTO, "client/LiveWater/LWT_PartMenu.lua")
        lua.execute(MENU)
        lua.execute(r"""
        SUB = { options = {} }
        function SUB:addOption(text, target, fn, ...) local o = { text = text, fn = fn, args = { ... } }
            table.insert(self.options, o) return o end
        ISContextMenu = { getNew = function() return SUB end }
        STATE = { type = "LiveWater:SprinklerAuto", data = {} }
        click({ "batman_livewater_01_56" }, {})
        """)
        texts = list(lua.eval("texts()").values())
        self.assertIn("ContextMenu_LWT_SetTimer", texts)
        self.assertIn("ContextMenu_LWT_OpenValve", texts)
        lua.execute("local o = SUB.options[5] o.fn(MENU_PLAYER, o.args[1], o.args[2], o.args[3])")
        self.assertEqual(lua.eval("SUB.options[5].text"), "ContextMenu_LWT_EveryHours|6")
        self.assertEqual(lua.eval("SENT[1][2]"), "setTimer")
        self.assertEqual(lua.eval("SENT[1][3].hours"), 6)
        self.assertEqual(lua.eval("SENT[1][3].x"), 4)


class LiveWireSummary(unittest.TestCase):
    def test_the_timer_is_a_consumer_but_not_counted_as_a_pump(self):
        lua = services(new_lua, POND, SPRINKLER, AUTO)
        lua.execute(r"""
        REGISTERED = {}
        LW = { revision = 6, registerConsumer = function(id, def) REGISTERED[id] = def return true end,
            consumerPowered = function() return true end }
        POW = require("LiveWater/LWT_Power").new({ catalog = LiveWater.Parts, world = WORLD })
        POW:register(LW)
        place("LiveWater:PondPump", 0, 0) place("LiveWater:SprinklerAuto", 3, 3, "batman_livewater_01_56")
        WORLD:writeState(3, 3, 0, "LiveWater:SprinklerAuto", { type = "LiveWater:SprinklerAuto", data = {} })
        WORLD:writeState(0, 0, 0, "LiveWater:PondPump", { type = "LiveWater:PondPump", data = {} })
        DEF = REGISTERED.LiveWater_LiveWater_SprinklerAuto
        A = WORLD:object(0, 0, 0, "LiveWater:PondPump") B = WORLD:object(3, 3, 0, "LiveWater:SprinklerAuto")
        SUM = DEF.summary({ A, B })
        """)
        self.assertEqual(lua.eval("DEF.powerConsumption(B)"), 5)
        self.assertEqual(list(lua.eval("SUM.lines[1]").values()), ["IGUI_LWT_LW_Pumps", 0, 1])


class Texts(unittest.TestCase):
    def test_scripts_sandbox_and_translations(self):
        with open(os.path.join(MEDIA, "scripts", "LWT_moveables.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"item Mov_LiveWater_SprinklerAuto\s*\{[^}]*WorldObjectSprite = batman_livewater_01_56,")
        with open(os.path.join(MEDIA, "scripts", "LWT_recipes.txt"), encoding="ascii") as f:
            recipe = re.search(r"(?s)craftRecipe LWTUpgradeSprinkler\s*\{.*?\n    \}", f.read()).group(0)
        self.assertIn("SkillRequired = Electricity:2,", recipe)
        self.assertIn("item 1 [Base.Mov_LiveWater_Sprinkler]", recipe)
        self.assertIn("item 1 Base.Mov_LiveWater_SprinklerAuto,", recipe)
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="ascii") as f:
            text = f.read()
        self.assertRegex(text, r"option LiveWater\.SprinklerTimerMin\s*\{\s*type = integer,[^}]*default = 1,")
        self.assertRegex(text, r"option LiveWater\.SprinklerTimerMax\s*\{\s*type = integer,[^}]*default = 24,")
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            self.assertIn("ContextMenu_LWT_SetTimer", load("ContextMenu.json"), lang)
            self.assertIn("ContextMenu_LWT_EveryHours", load("ContextMenu.json"), lang)
            for key in ("IGUI_LWT_Timer_Every", "IGUI_LWT_Timer_NoPower", "IGUI_LWT_OutOfBounds"):
                self.assertIn(key, load("IG_UI.json"), lang)
            self.assertIn("Sandbox_LWT_SprinklerTimerMin", load("Sandbox.json"), lang)
            self.assertIn("LWTUpgradeSprinkler", load("Recipes.json"), lang)


if __name__ == "__main__":
    unittest.main()
