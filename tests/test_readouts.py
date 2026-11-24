"""G04 (ADR-008 D03, D05-D07): readouts of the network. The meter and the pump add up their litres since they were set
down (`total`, kept by a part picked up and set down again, mirrored to the clients when it changes); "Information" on
them opens a window chosen by data (the `panel` hook): a water meter with rolling digits, an LCD screen for the pump;
the other parts keep their tooltip. A fixture fed by a LiveWater relay shows its water; the network view highlights the
fixtures of the area of each inlet of the network by how they get water (fed, dry, not plumbed, something else)."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
import test_inlet
import test_meter

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
METER = "shared/LiveWater/Parts/LWT_PartFlowMeter.lua"
SPRINKLER = "shared/LiveWater/Parts/LWT_PartSprinkler.lua"
INLET = "shared/LiveWater/Parts/LWT_PartHouseInlet.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"
LANGS = ("CN", "DE", "EN", "ES", "FR", "JP", "KO", "PT", "PTBR", "RU", "TR")


def values(t):
    return [t[i] for i in range(1, len(t) + 1)]


class MeterTotal(unittest.TestCase):
    def test_the_meter_adds_up_its_litres_and_mirrors_the_total(self):
        lua = test_meter.bench()
        lua.execute('NEED["2,0"] = 30 CLOCK:tick() NEED["2,0"] = 12 CLOCK:tick()')
        self.assertEqual(lua.eval("METER.data.meter.total"), 42)
        self.assertEqual(lua.eval("METER.data.meter.litres"), 12)
        self.assertEqual(lua.eval('WORLD:stateOf(1, 0, 0, "LiveWater:FlowMeter").data.meter.total'), 42)
        lua.execute('NEED["2,0"] = 0 CLOCK:tick()')
        self.assertEqual(lua.eval("METER.data.meter.total"), 42)

    def test_the_same_flow_again_is_mirrored_again(self):
        lua = test_meter.bench()
        lua.execute('NEED["2,0"] = 10 CLOCK:tick() CLOCK:tick()')
        self.assertEqual(lua.eval('WORLD:stateOf(1, 0, 0, "LiveWater:FlowMeter").data.meter.total'), 20)

    def test_a_meter_set_down_again_keeps_its_total(self):
        lua = test_meter.bench()
        lua.execute(r"""
        PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function() end, WORLD)
        WORLD:createPart(5, 5, 0, "batman_livewater_01_20")
        WORLD.states["5,5,0"] = { type = "LiveWater:FlowMeter", data = { meter = { total = 500 } } }
        PLACEMENT:added("batman_livewater_01_20", 5, 5, 0)
        """)
        self.assertEqual(lua.eval("REG:at(5, 5, 0).data.meter.total"), 500)

    def test_the_meter_asks_for_the_counter_window_with_its_whole_litres(self):
        lua = test_meter.bench()
        lua.execute('NEED["2,0"] = 7.6 CLOCK:tick()')
        self.assertEqual(values(lua.eval('{ LiveWater.Parts:first(METER, "panel") }')),
                         ["counter", "IGUI_LWT_Window_Meter", 7])


PUMP_BENCH = r"""
POWER = { powered = function() return true end }
NEED = {}
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, power = POWER, publisher = PUB,
    need = function(part) return NEED[part.x .. "," .. part.y] or 0 end })
place("LiveWater:PondPump", 0, 0) place("Test:Spr", 1, 0)
PUMP = REG:at(0, 0, 0)
"""


class PumpTotal(unittest.TestCase):
    def bench(self):
        lua = services(new_lua, POND)
        lua.execute(PUMP_BENCH)
        return lua

    def test_the_pump_adds_up_what_it_pumped(self):
        lua = self.bench()
        lua.execute('NEED["1,0"] = 80 CLOCK:tick() NEED["1,0"] = 20 CLOCK:tick() NEED["1,0"] = 0 CLOCK:tick()')
        self.assertEqual(lua.eval("PUMP.data.pump.total"), 70)
        self.assertEqual(lua.eval('WORLD:stateOf(0, 0, 0, "LiveWater:PondPump").data.pump.total'), 70)

    def test_the_lines_of_the_screen(self):
        lua = self.bench()
        lua.execute(r"""
        PART = { type = "LiveWater:PondPump", data = { intake = { source = "water" },
            pump = { running = true, litres = 20, efficiency = 50, total = 1234.6 } } }
        LINES = LiveWater.Parts:lines(PART, { scale = function(name) return name == "PumpFlowMultiplier" and 2 or 1 end })
        """)
        lines = [values(lua.eval("LINES[%d]" % i)) for i in range(1, lua.eval("#LINES") + 1)]
        self.assertEqual(lines, [["IGUI_LWT_Pump_Running"], ["IGUI_LWT_Pump_Possible", 50], ["IGUI_LWT_Pump_Flow", 20],
                                 ["IGUI_LWT_Pump_Total", 1235], ["IGUI_LWT_Pump_Efficiency", 50],
                                 ["IGUI_LWT_Source_water"]])

    def test_the_pump_asks_for_the_lcd_window(self):
        lua = self.bench()
        self.assertEqual(values(lua.eval('{ LiveWater.Parts:first(PUMP, "panel") }')), ["lcd", "IGUI_LWT_Window_Pump"])


# Client stubs of the windows: ISCollapsableWindow, text measures, the clock.
WINDOW = r"""
NOW = 0
function getTimestampMs() return NOW end
function getText(key, a, b)
    local s = key
    if a ~= nil then s = s .. "|" .. tostring(a) end
    if b ~= nil then s = s .. "|" .. tostring(b) end
    return s
end
UIFont = { Small = "Small", Medium = "Medium", Large = "Large", Code = "Code" }
DRAWN = {}
function getTextManager()
    return { MeasureStringX = function(_, font, s) return #s * 7 end, getFontHeight = function(_, font) return 15 end }
end
function getPlayerScreenLeft() return 0 end
function getPlayerScreenTop() return 0 end
ISCollapsableWindow = { TitleBarHeight = function() return 16 end }
ISCollapsableWindow.__index = ISCollapsableWindow
function ISCollapsableWindow:derive(name)
    local o = setmetatable({}, self)
    self.__index = self
    o.Type = name
    return o
end
function ISCollapsableWindow:new(x, y, w, h)
    local o = setmetatable({ x = x, y = y, width = w, height = h, visible = true }, self)
    self.__index = self
    return o
end
function ISCollapsableWindow:initialise() end
function ISCollapsableWindow:addToUIManager() self.added = true end
function ISCollapsableWindow:removeFromUIManager() self.added = false end
function ISCollapsableWindow:setVisible(v) self.visible = v end
function ISCollapsableWindow:setTitle(t) self.title = t end
function ISCollapsableWindow:setResizable() end
function ISCollapsableWindow:setWidth(w) self.width = w end
function ISCollapsableWindow:setHeight(h) self.height = h end
function ISCollapsableWindow:titleBarHeight() return 16 end
function ISCollapsableWindow:update() end
function ISCollapsableWindow:render() end
function ISCollapsableWindow:drawRect(...) table.insert(DRAWN, { "rect", ... }) end
function ISCollapsableWindow:drawRectBorder(...) table.insert(DRAWN, { "border", ... }) end
function ISCollapsableWindow:drawText(s, ...) table.insert(DRAWN, { "text", s, ... }) end
function ISCollapsableWindow:drawTextCentre(s, ...) table.insert(DRAWN, { "text", s, ... }) end
function ISCollapsableWindow:drawTextureScaled(tex, ...) table.insert(DRAWN, { "texture", tex, ... }) end
function ISCollapsableWindow:DrawTextureAngle(tex, ...) table.insert(DRAWN, { "turned", tex, ... }) end
TEXTURES = {}
function getTexture(path) return TEXTURES[path] end
function drawn(kind)
    for _, d in ipairs(DRAWN) do if d[1] == kind then return d end end
end
function colourOf(s)
    for _, d in ipairs(DRAWN) do if d[1] == "text" and d[2] == s then return { d[5], d[6], d[7] } end end
end
STATE = nil
SQUARE = { getX = function() return 4 end, getY = function() return 5 end, getZ = function() return 0 end }
OBJ = { square = SQUARE }
function OBJ:getSquare() return self.square end
function OBJ:getModData() return { movableData = { LiveWater = STATE } } end
PLAYER = { x = 4, y = 6, z = 0 }
function PLAYER:getX() return self.x end
function PLAYER:getY() return self.y end
function PLAYER:getZ() return self.z end
function PLAYER:getPlayerNum() return 0 end
function texts()
    local out = {}
    for _, d in ipairs(DRAWN) do if d[1] == "text" then table.insert(out, d[2]) end end
    return out
end
"""


def window_lua():
    lua = new_lua(API, METER, POND)
    lua.execute(WINDOW)
    lua.execute('Window = require("LiveWater/LWT_PartWindow") Counter = require("LiveWater/LWT_FaceCounter")'
                ' LcdFace = require("LiveWater/LWT_FaceLcd") Lcd = require("LiveWater/LWT_Lcd")')
    return lua


class Odometer(unittest.TestCase):
    def test_whole_litres_on_seven_rolls_that_turn_over(self):
        lua = window_lua()
        self.assertEqual(values(lua.eval("Counter.digits(1234.9, 7)")), ["0", "0", "0", "1", "2", "3", "4"])
        self.assertEqual(values(lua.eval("Counter.digits(12345678, 7)")), ["2", "3", "4", "5", "6", "7", "8"])
        self.assertEqual(values(lua.eval("Counter.digits(nil, 7)")), ["0"] * 7)
        self.assertEqual(lua.eval("Counter.ROLLS"), 7)


class Windows(unittest.TestCase):
    def test_the_meter_window_shows_the_total_on_its_rolls_and_its_lines(self):
        lua = window_lua()
        lua.execute(r"""
        STATE = { type = "LiveWater:FlowMeter", data = { meter = { total = 321, litres = 12, quality = "clean" } } }
        W = Window.open(PLAYER, OBJ, "LiveWater:FlowMeter", Counter)
        W:render()
        """)
        self.assertTrue(lua.eval("W.added"))
        self.assertEqual(lua.eval("W.title"), "IGUI_LWT_Window_Meter")
        drawn = values(lua.eval("texts()"))
        self.assertEqual(drawn[:7], ["0", "0", "0", "0", "3", "2", "1"])
        self.assertIn("IGUI_LWT_Meter_Total|321", drawn)
        self.assertIn("IGUI_LWT_Meter_Flow|12", drawn)
        self.assertIn("IGUI_LWT_Meter_Water_clean", drawn)
        self.assertIsNone(lua.eval('drawn("texture")'))

    def test_the_dial_image_the_rolls_over_it_and_the_hand_turning_every_ten_litres(self):
        lua = window_lua()
        lua.execute(r"""
        TEXTURES[Counter.FACE_TEXTURE] = "face" TEXTURES[Counter.HAND_TEXTURE] = "hand" Counter.reload()
        STATE = { type = "LiveWater:FlowMeter", data = { meter = { total = 1237.9, litres = 4, quality = "tainted" } } }
        W = Window.open(PLAYER, OBJ, "LiveWater:FlowMeter", Counter)
        W:render()
        """)
        face = values(lua.eval('drawn("texture")'))
        self.assertEqual(face[1], "face")
        self.assertEqual(face[4:6], [lua.eval("Counter.DIAL")] * 2)
        hand = values(lua.eval('drawn("turned")'))
        self.assertEqual(hand[1], "hand")
        self.assertAlmostEqual(hand[4], 252)
        self.assertEqual(values(lua.eval("texts()"))[:7], ["0", "0", "0", "1", "2", "3", "7"])
        amber = values(lua.eval('colourOf("IGUI_LWT_Meter_Water_tainted")'))
        self.assertEqual(amber, values(lua.eval("Counter.AMBER")))
        self.assertLess(amber[2], amber[0])
        self.assertGreater(amber[1], 0.3)

    def test_an_open_window_reads_the_mirror_again_at_its_pace_only(self):
        lua = window_lua()
        lua.execute(r"""
        STATE = { type = "LiveWater:FlowMeter", data = { meter = { total = 1 } } }
        W = Window.open(PLAYER, OBJ, "LiveWater:FlowMeter", Counter)
        STATE = { type = "LiveWater:FlowMeter", data = { meter = { total = 99 } } }
        NOW = Window.REFRESH_MS - 1 W:update()
        """)
        self.assertEqual(lua.eval("W.view.reading"), 1)
        lua.execute("NOW = Window.REFRESH_MS W:update()")
        self.assertEqual(lua.eval("W.view.reading"), 99)

    def test_the_window_closes_when_the_part_is_gone_or_the_player_walked_away(self):
        lua = window_lua()
        lua.execute(r"""
        STATE = { type = "LiveWater:FlowMeter", data = {} }
        W = Window.open(PLAYER, OBJ, "LiveWater:FlowMeter", Counter)
        OBJ.square = nil NOW = Window.REFRESH_MS W:update()
        """)
        self.assertFalse(lua.eval("W.added"))
        self.assertIsNone(lua.eval("Window.instance"))
        lua.execute(r"""
        OBJ.square = SQUARE NOW = 0
        W = Window.open(PLAYER, OBJ, "LiveWater:FlowMeter", Counter)
        PLAYER.x = 40 NOW = Window.REFRESH_MS W:update()
        """)
        self.assertFalse(lua.eval("W.added"))

    def test_one_window_at_a_time(self):
        lua = window_lua()
        lua.execute(r"""
        STATE = { type = "LiveWater:FlowMeter", data = {} }
        A = Window.open(PLAYER, OBJ, "LiveWater:FlowMeter", Counter)
        B = Window.open(PLAYER, OBJ, "LiveWater:FlowMeter", Counter)
        """)
        self.assertFalse(lua.eval("A.added"))
        self.assertTrue(lua.eval("B.added"))

    def test_the_pump_screen_shows_its_lines_and_grows_to_fit_them(self):
        lua = window_lua()
        lua.execute(r"""
        STATE = { type = "LiveWater:PondPump", data = { pump = { running = true, litres = 20, total = 70 } } }
        W = Window.open(PLAYER, OBJ, "LiveWater:PondPump", LcdFace)
        W:render()
        WIDTH = W.width
        STATE = { type = "LiveWater:PondPump", data = { pump = { running = true, litres = 20, total = 70 },
            intake = { source = "a_much_longer_source_name_than_any_line_before_it_on_this_screen" } } }
        NOW = Window.REFRESH_MS W:update()
        """)
        drawn = values(lua.eval("texts()"))
        for line in ("IGUI_LWT_Pump_Running", "IGUI_LWT_Pump_Possible|50", "IGUI_LWT_Pump_Flow|20",
                     "IGUI_LWT_Pump_Total|70", "IGUI_LWT_Pump_Efficiency|100"):
            self.assertIn(line, drawn)
        self.assertEqual(lua.eval("W.title"), "IGUI_LWT_Window_Pump")
        self.assertGreater(lua.eval("W.width"), lua.eval("WIDTH"))

    def test_the_lcd_font_has_the_glyphs_of_chinese_japanese_and_korean(self):
        lua = window_lua()
        for lang in ("CN", "CH", "JP", "KO", "TH"):
            self.assertEqual(lua.eval('Lcd.fontFor("%s")' % lang), "Small", lang)
        for lang in ("EN", "FR", "RU"):
            self.assertEqual(lua.eval('Lcd.fontFor("%s")' % lang), "Code", lang)

    def test_no_per_frame_event(self):
        lua = window_lua()
        for name in ("OnTick", "OnPlayerUpdate", "OnRenderTick", "OnPostRender", "OnPreUIDraw"):
            self.assertEqual(lua.eval("#Events.%s.handlers" % name), 0, name)


MENU = r"""
OPENED = {}
Panels = require("LiveWater/LWT_Panels")
function getText(key, a) if a ~= nil then return key .. "|" .. tostring(a) end return key end
ISToolTip = { new = function() return { initialise = function() end, setName = function() end } end }
function getItemNameFromFullType(t) return t end
STATE = nil
local function object(sprite)
    return { getSpriteName = function() return sprite end,
             getModData = function() return { movableData = { LiveWater = STATE } } end }
end
PLAYER = { getInventory = function() return { containsTypeRecurse = function() return false end } end }
function getSpecificPlayer() return PLAYER end
function click(sprite)
    local objs = { object(sprite) }
    local sq = { getX = function() return 4 end, getY = function() return 5 end, getZ = function() return 0 end,
        getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
    OPTIONS = {}
    local context = { addOption = function(self, text, target, fn, ...)
        local o = { text = text, run = function(...) fn(target, ...) end, args = { ... } }
        table.insert(OPTIONS, o) return o end }
    fire("OnFillWorldObjectContextMenu", 0, context, { { getSquare = function() return sq end } }, false)
end
function option(text) for _, o in ipairs(OPTIONS) do if o.text == text then return o end end end
"""


class InformationMenu(unittest.TestCase):
    def menu(self):
        lua = new_lua(API, METER, POND, SPRINKLER, "client/LiveWater/LWT_PartMenu.lua")
        lua.execute(MENU)
        return lua

    def test_a_part_whose_capability_names_a_window_opens_it(self):
        lua = self.menu()
        lua.execute(r"""
        Panels.register("counter", { name = "counter face" })
        Panels.window = function(player, obj, typeId, face) table.insert(OPENED, { player, typeId, face.name }) end
        STATE = { type = "LiveWater:FlowMeter", data = { meter = { total = 5 } } }
        click("batman_livewater_01_20")
        local o = option("ContextMenu_LWT_Info") o.run(unpack(o.args))
        """)
        self.assertIsNone(lua.eval('option("ContextMenu_LWT_Info").toolTip'))
        self.assertEqual(lua.eval("OPENED[1][2]"), "LiveWater:FlowMeter")
        self.assertEqual(lua.eval("OPENED[1][3]"), "counter face")
        self.assertTrue(lua.eval("OPENED[1][1] == PLAYER"))

    def test_the_other_parts_keep_their_tooltip(self):
        lua = self.menu()
        lua.execute(r"""
        Panels.register("counter", { name = "counter face" })
        STATE = { type = "LiveWater:Sprinkler", data = {} }
        click("batman_livewater_01_48")
        """)
        self.assertIsNotNone(lua.eval('option("ContextMenu_LWT_Info").toolTip'))

    def test_a_window_kind_nobody_registered_falls_back_to_the_tooltip(self):
        lua = self.menu()
        lua.execute('STATE = { type = "LiveWater:PondPump", data = {} } click("batman_livewater_01_24")')
        self.assertIsNotNone(lua.eval('option("ContextMenu_LWT_Info").toolTip'))

    def test_registering_a_face_twice_is_refused(self):
        lua = self.menu()
        self.assertTrue(lua.eval('Panels.register("lcd", {})'))
        self.assertFalse(lua.eval('Panels.register("lcd", {})'))
        self.assertFalse(lua.eval('Panels.register("bad", nil)'))


FIXTURE = r"""
function getText(key, a, b)
    local s = key
    if a ~= nil then s = s .. "|" .. tostring(a) end
    if b ~= nil then s = s .. "|" .. tostring(b) end
    return s
end
function instanceof() return false end
ItemTag = { PIPE_WRENCH = "PipeWrenchTag" }
PLAYER = nil
function getSpecificPlayer() return PLAYER end
function item(type, broken)
    return { getType = function() return type end, isBroken = function() return broken == true end,
        hasTag = function() return false end }
end
function inventory(list)
    local inv = { list = list or {} }
    function inv:getFirstTypeEvalRecurse(type, fn)
        for i = 1, #self.list do
            local it = self.list[i]
            if it:getType() == type and fn(it) then return it end
        end
        return nil
    end
    function inv:getFirstTagEvalRecurse(tag, fn) return nil end
    return inv
end
function wrenchPlayer(list)
    local inv = inventory(list)
    PLAYER = { getInventory = function() return inv end }
end
IsoFlagType = { waterPiped = "waterPiped" }
function getGameTime() return { getWorldAgeDaysSinceBegin = function() return 100 end } end
function getSandboxOptions() return { getWaterShutModifier = function() return 0 end } end
SRC = nil
IsoObject = { FindExternalWaterSource = function(sq) return SRC end }
function relay(litres, mark)
    local md = { [mark or "LiveWaterRelay"] = { v = 1, inlet = "5,9,0" } }
    return { hasModData = function() return true end, getModData = function() return md end,
        getFluidContainer = function() return { getCapacity = function() return litres end } end }
end
FIX = { amount = 0, plumbed = true }
function FIX:getSprite() return { getProperties = function() return { has = function() return true end } end } end
function FIX:getSpriteName() return nil end
function FIX:getFluidAmount() return self.amount end
function FIX:getUsesExternalWaterSource() return self.plumbed end
function FIX:hasModData() return true end
function FIX:getModData() return {} end
SQ = { getObjects = function() return { size = function() return 1 end, get = function() return FIX end } end }
function menu()
    OPTIONS = {}
    local context = { addOption = function(self, text) local o = { text = text } table.insert(OPTIONS, o) return o end }
    fire("OnFillWorldObjectContextMenu", 0, context, { { getSquare = function() return SQ end } }, false)
end
"""


class FixtureWater(unittest.TestCase):
    def menu(self):
        lua = new_lua(API, "client/LiveWater/LWT_FixtureMenu.lua")
        lua.execute(FIXTURE)
        return lua

    def test_a_fixture_fed_by_a_relay_shows_its_water(self):
        lua = self.menu()
        lua.execute("SRC = relay(25) FIX.amount = 17.5 menu()")
        self.assertEqual(lua.eval("#OPTIONS"), 1)
        self.assertEqual(lua.eval("OPTIONS[1].text"), "ContextMenu_LWT_Water|17.5|25")
        # information, not a fault: greyed, never the red of an unavailable option
        self.assertTrue(lua.eval("OPTIONS[1].isDisabled"))
        self.assertFalse(lua.eval("OPTIONS[1].notAvailable"))

    def test_a_dry_fixture_still_says_why(self):
        lua = self.menu()
        lua.execute("SRC = relay(25) FIX.amount = 0 menu()")
        self.assertEqual(lua.eval("OPTIONS[1].text"), "ContextMenu_LWT_NoWater|IGUI_LWT_Why_Waiting")
        self.assertTrue(lua.eval("OPTIONS[1].notAvailable"))

    def test_water_from_something_else_shows_no_line(self):
        lua = self.menu()
        lua.execute('SRC = relay(25, "LiveWireRelay") FIX.amount = 10 menu()')
        self.assertEqual(lua.eval("#OPTIONS"), 0)


class FixtureWrenchHint(unittest.TestCase):
    """A fixture left to plumb says when the local player carries no pipe wrench, or only a broken
    one: the game's own "Pipe Wrench required." hides it (player report of 2026-11-24)."""

    def menu(self):
        lua = new_lua(API, "client/LiveWater/LWT_FixtureMenu.lua")
        lua.execute(FIXTURE)
        return lua

    def line(self, wrenches):
        lua = self.menu()
        lua.execute('FIX.plumbed = false SRC = relay(25) FIX.amount = 0 wrenchPlayer(%s) menu()' % wrenches)
        return lua, lua.eval("OPTIONS[1].text")

    def test_no_pipe_wrench_is_named(self):
        lua, text = self.line('{ item("Wrench") }')
        self.assertEqual(text, "ContextMenu_LWT_NoWater|IGUI_LWT_Why_NotPlumbed. IGUI_LWT_NoWrench")
        self.assertTrue(lua.eval("OPTIONS[1].notAvailable"))

    def test_a_broken_pipe_wrench_is_named(self):
        lua, text = self.line('{ item("PipeWrench", true) }')
        self.assertEqual(text, "ContextMenu_LWT_NoWater|IGUI_LWT_Why_NotPlumbed. IGUI_LWT_WrenchBroken")

    def test_a_usable_pipe_wrench_adds_nothing(self):
        lua, text = self.line('{ item("PipeWrench") }')
        self.assertEqual(text, "ContextMenu_LWT_NoWater|IGUI_LWT_Why_NotPlumbed")

    def test_a_plumbed_fixture_keeps_its_own_reason(self):
        lua = self.menu()
        lua.execute('FIX.plumbed = true SRC = relay(25) FIX.amount = 0 wrenchPlayer({ item("Wrench") }) menu()')
        self.assertEqual(lua.eval("OPTIONS[1].text"), "ContextMenu_LWT_NoWater|IGUI_LWT_Why_Waiting")


class FixtureStates(unittest.TestCase):
    """The authority sorts the fixtures of an inlet's area; showNetwork sends them with the parts."""

    def bench(self):
        lua = test_inlet.bench()
        lua.execute(r"""
        PLUMB:addFixture(2, 12, 0) PLUMB:addFixture(2, 16, 0) PLUMB:addFixture(8, 12, 0, false)
        PLUMB:addFixture(7, 17, 0) PLUMB.other["7,17,1"] = true
        place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()
        PLUMB.relays["2,12,1"].amount = 10
        INLET_PART = REG:at(5, 9, 0)
        function statusAt(list, x, y)
            for _, f in ipairs(list) do if f.x == x and f.y == y then return f.status end end
        end
        """ % TILE)
        return lua

    def test_fed_dry_not_plumbed_and_other(self):
        lua = self.bench()
        lua.execute("LIST = RELAYS:fixtureStates(INLET_PART)")
        self.assertEqual(lua.eval("#LIST"), 4)
        self.assertEqual(lua.eval("statusAt(LIST, 2, 12)"), "fed")
        self.assertEqual(lua.eval("statusAt(LIST, 2, 16)"), "dry")
        self.assertEqual(lua.eval("statusAt(LIST, 8, 12)"), "notPlumbed")
        self.assertEqual(lua.eval("statusAt(LIST, 7, 17)"), "other")

    def test_show_network_sends_the_fixtures_of_its_inlets(self):
        lua = self.bench()
        lua.execute(r"""
        REPLIES = {}
        CMDS = require("LiveWater/LWT_Commands").new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD,
            players = PLAYERS, relays = RELAYS,
            replies = { to = function(self, player, command, args) table.insert(REPLIES, { command, args }) end } })
        CMDS:register("showNetwork", require("LiveWater/Commands/LWT_CmdShowNetwork"))
        OK = CMDS:dispatch(newPlayer(5, 9, 0), "showNetwork", { x = 5, y = 9, z = 0 })
        SENT = REPLIES[1][2]
        """)
        self.assertTrue(lua.eval("OK"))
        self.assertEqual(lua.eval("#SENT.parts"), 1)
        self.assertEqual(lua.eval("#SENT.fixtures"), 4)
        self.assertEqual(lua.eval("statusAt(SENT.fixtures, 2, 16)"), "dry")
        self.assertEqual(lua.eval("SENT.fixtures[1].z"), 0)


VIEW_FIXTURES = r"""
function instanceof() return false end
IsoFlagType = { waterPiped = "waterPiped" }
function newFixture()
    local o = newObject("fixtures_sinks_01_0")
    o.getSprite = function() return { getProperties = function() return { has = function() return true end } end } end
    return o
end
FIXTURES = {}
for i, s in ipairs({ "fed", "dry", "notPlumbed", "other" }) do
    FIXTURES[s] = newFixture()
    newSquare(10 + i, 0, { FIXTURES[s] })
end
FIXTURE_LIST = { { x = 11, y = 0, z = 0, status = "fed" }, { x = 12, y = 0, z = 0, status = "dry" },
    { x = 13, y = 0, z = 0, status = "notPlumbed" }, { x = 14, y = 0, z = 0, status = "other" } }
"""


class NetworkViewFixtures(unittest.TestCase):
    def view(self):
        from test_interface import VIEW
        lua = new_lua(API, "shared/LiveWater/Parts/LWT_PartPipe.lua", SPRINKLER, INLET,
                      "client/LiveWater/LWT_NetworkView.lua")
        lua.execute(VIEW)
        lua.execute(VIEW_FIXTURES)
        return lua

    def test_fixtures_are_highlighted_by_how_they_get_water_and_counted(self):
        lua = self.view()
        lua.execute('fire("OnServerCommand", "LiveWater", "network", { parts = { { x = 2, y = 0, z = 0 } },'
                    ' fixtures = FIXTURE_LIST })')
        colours = {}
        for s in ("fed", "dry", "notPlumbed", "other"):
            self.assertTrue(lua.eval('FIXTURES["%s"].highlighted' % s), s)
            colours[s] = tuple(values(lua.eval('FIXTURES["%s"].color' % s))[:3])
        self.assertEqual(len(set(colours.values())), 4)
        self.assertGreater(colours["fed"][1], colours["fed"][0])
        self.assertGreater(colours["dry"][0], colours["dry"][1])
        lua.execute("menu(SQ)")
        legend = lua.eval('option("ContextMenu_LWT_HideNetwork")').toolTip.description
        for s in ("fed", "dry", "notPlumbed", "other"):
            self.assertIn("IGUI_LWT_View_fixtures_%s|1" % s, legend)
        lua.execute('local o = option("ContextMenu_LWT_HideNetwork") o.run(unpack(o.args))')
        self.assertFalse(lua.eval('FIXTURES["fed"].highlighted'))

    def test_a_network_without_fixtures_keeps_the_short_legend(self):
        lua = self.view()
        lua.execute('fire("OnServerCommand", "LiveWater", "network", { parts = { { x = 2, y = 0, z = 0 } } }) menu(SQ)')
        legend = lua.eval('option("ContextMenu_LWT_HideNetwork")').toolTip.description
        self.assertNotIn("IGUI_LWT_View_fixtures_fed", legend)
        self.assertIsNone(lua.eval('option("ContextMenu_LWT_ShowNetwork")'))


NEW_KEYS = {
    "IG_UI.json": {"IGUI_LWT_Window_Meter": "", "IGUI_LWT_Window_Pump": "", "IGUI_LWT_Meter_Total": "%1",
                   "IGUI_LWT_Pump_Possible": "%1", "IGUI_LWT_Pump_Total": "%1",
                   "IGUI_LWT_View_fixtures_fed": "%1", "IGUI_LWT_View_fixtures_dry": "%1",
                   "IGUI_LWT_View_fixtures_notPlumbed": "%1", "IGUI_LWT_View_fixtures_other": "%1"},
    "ContextMenu.json": {"ContextMenu_LWT_Water": "%2"},
}


class Texts(unittest.TestCase):
    def test_every_new_text_in_the_eleven_languages(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in LANGS:
            for name, keys in NEW_KEYS.items():
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    found = json.load(f)
                for key, arg in keys.items():
                    self.assertTrue(key in found, (lang, key))
                    self.assertTrue(arg in found[key], (lang, key))


if __name__ == "__main__":
    unittest.main()
