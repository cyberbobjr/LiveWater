"""E08: pond pump and power (ADR-001 D16, D20): sprites drawn by state and facing (variants), placement next to
natural water only, 50 L per step, 250 W while running, Live Wire consumer (revision 6 or later) or the vanilla
power rule, no work without power, the sprite follows the real state, the state is mirrored on the object."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


def api():
    lua = new_lua(API)
    lua.execute("LOG = {} print = function(s) LOG[#LOG + 1] = s end")
    return lua


VARIED = ('{ variants = { off = { "v_off_s", "v_off_e" }, on = { "v_on_s", "v_on_e" } },'
          ' capabilities = { pump = true } }')


class Variants(unittest.TestCase):
    def test_a_part_drawn_by_state_needs_no_mask_sprites(self):
        lua = api()
        self.assertEqual(call(lua, 'LiveWater.API.registerPart("Test:V", %s)' % VARIED), (True, None))
        self.assertEqual(lua.eval('LiveWater.Parts:typeOfSprite("v_on_e")'), "Test:V")
        self.assertEqual(lua.eval('LiveWater.Parts:facingOf("v_on_e")'), 2)
        self.assertEqual(lua.eval('LiveWater.Parts:variant("Test:V", "off", 2)'), "v_off_e")
        self.assertFalse(lua.eval('LiveWater.Parts:hasShape("Test:V", 0)'))
        d = lua.eval('LiveWater.API.part("Test:V")')
        self.assertEqual(d.variants.on[1], "v_on_s")

    def test_invalid_or_duplicate_variants_are_refused(self):
        lua = api()
        lua.execute('LiveWater.API.registerPart("Test:V", %s)' % VARIED)
        self.assertEqual(call(lua, 'LiveWater.API.registerPart("Test:W", { variants = { on = { "v_on_s" } },'
                                   ' capabilities = { pump = true } })'), (False, "duplicate_sprite"))
        self.assertEqual(call(lua, 'LiveWater.API.registerPart("Test:X", { variants = { ["bad key"] = { "x" } },'
                                   ' capabilities = { pump = true } })'), (False, "invalid_variants"))
        self.assertEqual(call(lua, 'LiveWater.API.registerPart("Test:Y", { variants = { on = { "a", "b", "c", "d", "e" } },'
                                   ' capabilities = { pump = true } })'), (False, "invalid_variants"))
        self.assertEqual(call(lua, 'LiveWater.API.registerPart("Test:Z", { capabilities = { pump = true } })'),
                         (False, "invalid_sprites"))

    def test_the_look_joins_the_tokens_of_the_capabilities(self):
        lua = api()
        lua.execute('LiveWater.API.registerPart("Test:V", %s)' % VARIED)
        self.assertEqual(lua.eval('LiveWater.Parts:look({ type = "Test:V", data = {} })'), "off")
        self.assertEqual(lua.eval('LiveWater.Parts:look({ type = "Test:V", data = { pump = { running = true } } })'), "on")


class PondPumpPart(unittest.TestCase):
    def test_definition_follows_the_tile_contract_and_the_adr(self):
        lua = new_lua(API, POND)
        d = lua.eval('LiveWater.API.part("LiveWater:PondPump")')
        for key, base in (("off", 24), ("on", 28)):
            self.assertEqual([d.variants[key][i] for i in range(1, 5)], [TILE + str(base + k) for k in range(4)], key)
        self.assertEqual((d.capabilities.pump.flow, d.capabilities.pump.watts), (50, 250))
        self.assertIsNotNone(d.capabilities.intake)


BENCH = r"""
POWER = { off = {} }
function POWER:powered(part) return not self.off[part.x .. "," .. part.y] end
NEED = {}
function newClock()
    PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
    CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
        catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, power = POWER, publisher = PUB,
        need = function(part) return NEED[part.x .. "," .. part.y] or 0 end })
end
newClock()
"""


def bench():
    lua = services(new_lua, POND)
    lua.execute(BENCH)
    return lua


class Siting(unittest.TestCase):
    def test_refused_away_from_natural_water(self):
        lua = bench()
        lua.execute('WORLD.dry["5,5,0"] = true')
        self.assertEqual(call(lua, 'TOPO:canAdd("LiveWater:PondPump", 5, 5, 0)'), (False, "no_source"))
        self.assertEqual(call(lua, 'place("LiveWater:PondPump", 5, 5, "%s24")' % TILE), (False, "no_source"))
        self.assertIsNone(lua.eval("REG:at(5, 5, 0)"))

    def test_accepted_next_to_water_and_the_source_is_recorded(self):
        lua = bench()
        self.assertTrue(lua.eval('place("LiveWater:PondPump", 0, 0, "%s25")' % TILE))
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.intake.source"), "water")

    def test_the_placement_rule_refuses_the_furniture_cursor_away_from_water(self):
        lua = new_lua(API, POND)
        lua.execute(r"""
        WET = {}
        IsoFlagType = { water = "water" }
        function sq(x, y, z)
            return { getX = function() return x end, getY = function() return y end, getZ = function() return z end,
                has = function(_, f) return f == "water" and WET[x .. "," .. y] == true end,
                getObjects = function() return { size = function() return 0 end } end }
        end
        function getCell() return { getGridSquare = function(_, x, y, z) return sq(x, y, z) end } end
        ISMoveableSpriteProps = { canPlaceMoveableInternal = function(self) return self.vanilla end,
            getInfoPanelDescription = function() return {} end,
            addLineToInfoTable = function(t, text) table.insert(t, text) return t end }
        function getText(k) return k end
        isServer = function() return false end
        RULES = require("LiveWater/LWT_PlaceRules")
        function can(sprite, x, vanilla)
            local props = setmetatable({ spriteName = sprite, vanilla = vanilla }, { __index = ISMoveableSpriteProps })
            return props:canPlaceMoveableInternal(nil, sq(x, 0, 0), nil)
        end
        """)
        self.assertFalse(lua.eval('can("%s24", 10, true)' % TILE))
        lua.execute('WET["11,1"] = true')
        self.assertTrue(lua.eval('can("%s24", 10, true)' % TILE))
        self.assertFalse(lua.eval('can("%s24", 10, false)' % TILE))
        self.assertTrue(lua.eval('can("crafted_01_0", 50, true)'))
        self.assertEqual(call(lua, 'RULES.check("%s24", sq(50, 0, 0))' % TILE), (False, "IGUI_LWT_NoSource"))


class Running(unittest.TestCase):
    def test_no_work_without_power(self):
        lua = bench()
        lua.execute("""
        place("LiveWater:PondPump", 0, 0, "%s25") place("Test:Spr", 1, 0)
        NEED["1,0"] = 5
        POWER.off["0,0"] = true
        EMITTED = {}
        CLOCK:tick()
        """ % TILE)
        self.assertEqual(len(lua.eval('emitted("waterDelivered")')), 0)
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.pump.powered"), False)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "25")

    def test_running_with_power_and_need_turns_the_sprite_on_keeping_its_facing(self):
        lua = bench()
        lua.execute("""
        place("LiveWater:PondPump", 0, 0, "%s25") place("Test:Spr", 1, 0)
        NEED["1,0"] = 80
        EMITTED = {}
        CLOCK:tick()
        """ % TILE)
        delivered = lua.eval('emitted("waterDelivered")')
        self.assertEqual(delivered[1][3], 50)
        self.assertTrue(lua.eval("REG:at(0, 0, 0).data.pump.running"))
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.pump.litres"), 50)
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "29")
        lua.execute('NEED["1,0"] = 0 CLOCK:tick()')
        self.assertFalse(lua.eval("REG:at(0, 0, 0).data.pump.running"))
        self.assertEqual(lua.eval("WORLD:sprite(0, 0, 0)"), TILE + "25")

    def test_two_pumps_share_the_water_delivered(self):
        lua = bench()
        lua.execute("""
        place("LiveWater:PondPump", 0, 0) place("Test:Spr", 1, 0) place("LiveWater:PondPump", 2, 0)
        NEED["1,0"] = 50
        CLOCK:tick()
        """)
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.pump.litres"), 25)
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.pump.litres"), 25)

    def test_the_flow_is_scaled_by_the_sandbox_multiplier(self):
        lua = bench()
        lua.execute("""
        CLOCK.ctx.scale = function(name) return name == "PumpFlowMultiplier" and 2 or 1 end
        place("LiveWater:PondPump", 0, 0) place("Test:Spr", 1, 0)
        NEED["1,0"] = 500
        EMITTED = {}
        CLOCK:tick()
        """)
        self.assertEqual(lua.eval('emitted("waterDelivered")')[1][3], 100)

    def test_the_state_is_mirrored_on_the_object_when_it_changes(self):
        lua = bench()
        lua.execute("""
        place("LiveWater:PondPump", 0, 0) place("Test:Spr", 1, 0)
        NEED["1,0"] = 10
        CLOCK:tick()
        """)
        state = lua.eval('WORLD:stateOf(0, 0, 0, "LiveWater:PondPump")')
        self.assertEqual(state.type, "LiveWater:PondPump")
        self.assertTrue(state.data.pump.running)
        lua.execute('NEED["1,0"] = 0 CLOCK:tick() WORLD.writes = 0 CLOCK:tick()')
        self.assertEqual(lua.eval("WORLD.writes"), 0)

    def test_a_pump_placed_again_keeps_its_mirrored_state(self):
        lua = bench()
        lua.execute("""
        PLACEMENT = require("LiveWater/LWT_Placement").new(TOPO, LiveWater.Parts, function() end, WORLD)
        WORLD:createPart(0, 0, 0, "%s24")
        WORLD.states["0,0,0"] = { type = "LiveWater:PondPump", data = { pump = { litres = 7 } } }
        PLACEMENT:added("%s24", 0, 0, 0)
        """ % (TILE, TILE))
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.pump.litres"), 7)
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.intake.source"), "water")


LIVEWIRE = r"""
REGISTERED = {}
function fakeLiveWire(revision)
    return { revision = revision,
        registerConsumer = function(id, def) REGISTERED[id] = def return true end,
        consumerPowered = function(obj) return obj.lw == true end }
end
Power = require("LiveWater/LWT_Power")
function newPower(api)
    POW = Power.new({ catalog = LiveWater.Parts, world = WORLD })
    return POW:register(api)
end
"""


class LiveWirePower(unittest.TestCase):
    def lw(self):
        lua = bench()
        lua.execute(LIVEWIRE)
        return lua

    def test_registered_only_from_revision_6(self):
        lua = self.lw()
        self.assertEqual(lua.eval("newPower(fakeLiveWire(5))"), 0)
        self.assertEqual(lua.eval("newPower(nil)"), 0)
        # Test:Pump of the fakes needs current too (pump capability)
        self.assertEqual(lua.eval("newPower(fakeLiveWire(6))"), 2)
        sprites = lua.eval('REGISTERED["LiveWater_LiveWater_PondPump"].sprites')
        names = [sprites[i] for i in range(1, len(sprites) + 1)]
        self.assertEqual(len(names), 8)
        self.assertIn(TILE + "29", names)

    def test_250_w_running_and_0_stopped(self):
        lua = self.lw()
        lua.execute("newPower(fakeLiveWire(6)) DEF = REGISTERED.LiveWater_LiveWater_PondPump")
        lua.execute("""
        place("LiveWater:PondPump", 0, 0) place("Test:Spr", 1, 0)
        OBJ = WORLD:object(0, 0, 0, "LiveWater:PondPump")
        """)
        self.assertEqual(lua.eval("DEF.powerConsumption(OBJ)"), 0)
        lua.execute('NEED["1,0"] = 10 CLOCK:tick()')
        self.assertEqual(lua.eval("DEF.powerConsumption(OBJ)"), 250)

    def test_display_and_summary_follow_the_live_wire_format(self):
        lua = self.lw()
        lua.execute("newPower(fakeLiveWire(6)) DEF = REGISTERED.LiveWater_LiveWater_PondPump")
        lua.execute("""
        place("LiveWater:PondPump", 0, 0) place("Test:Spr", 1, 0) place("LiveWater:PondPump", 10, 10)
        NEED["1,0"] = 10 CLOCK:tick()
        A = WORLD:object(0, 0, 0, "LiveWater:PondPump") B = WORLD:object(10, 10, 0, "LiveWater:PondPump")
        INFO = DEF.display(A)
        SUM = DEF.summary({ A, B })
        """)
        lines = lua.eval("INFO.lines")
        self.assertTrue(1 <= len(lines) <= 4)
        self.assertEqual(lines[1][1], "IGUI_LWT_Pump_Running")
        self.assertEqual(lua.eval("#SUM.lines"), 2)
        self.assertEqual(list(lua.eval("SUM.lines[1]").values()), ["IGUI_LWT_LW_Pumps", 1, 2])
        self.assertEqual(list(lua.eval("SUM.lines[2]").values()), ["IGUI_LWT_LW_Flow", 10])
        for expr in ("INFO.lines[1][1]", "SUM.lines[1][1]", "SUM.lines[2][1]"):
            self.assertRegex(lua.eval(expr), r"^[\w]{1,64}$")

    def test_powered_asks_live_wire_when_registered_else_the_vanilla_rule(self):
        lua = self.lw()
        lua.execute('place("LiveWater:PondPump", 0, 0) PART = REG:at(0, 0, 0)')
        lua.execute("newPower(nil)")
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute('WORLD.unpowered["0,0,0"] = true')
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute("newPower(fakeLiveWire(6))")
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))

    def test_a_pump_against_a_barrel_is_a_live_wire_consumer_too(self):
        # ADR-012 D05: whatever its source (pond, well, barrel), the pump takes its current from Live Wire
        lua = self.lw()
        lua.execute('WORLD.dry["0,0,0"] = true WORLD.vessels["0,0,0"] = true')
        self.assertTrue(lua.eval('place("LiveWater:PondPump", 0, 0)'))
        self.assertIsNone(lua.eval("REG:at(0, 0, 0).data.intake.source"))
        lua.execute("PART = REG:at(0, 0, 0)")
        self.assertEqual(lua.eval("newPower(fakeLiveWire(6))"), 2)
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))


class Wiring(unittest.TestCase):
    def test_live_wire_registration_waits_for_on_init_world(self):
        lua = new_lua(API, POND)
        lua.execute(r"""
        CALLS = 0
        LiveWire = { API = { revision = 6, registerConsumer = function() CALLS = CALLS + 1 return true end,
            consumerPowered = function() return false end } }
        """)
        from test_placement import GAME
        lua.execute(GAME)
        lua.execute('require("LiveWater/LWT_Server")')
        self.assertEqual(lua.eval("CALLS"), 0)
        lua.execute('fire("OnInitWorld")')
        self.assertEqual(lua.eval("CALLS"), 1)


def script(name):
    with open(os.path.join(MEDIA, "scripts", name), encoding="ascii") as f:
        return f.read()


class Scripts(unittest.TestCase):
    def test_moveable_item_and_recipe(self):
        text = script("LWT_moveables.txt")
        self.assertRegex(text, r"^module Base\b")
        self.assertRegex(text, r"item Mov_LiveWater_PondPump\s*\{[^}]*ItemType = base:moveable,[^}]*"
                               r"WorldObjectSprite = batman_livewater_01_24,")
        self.assertRegex(script("LWT_recipes.txt"), r"craftRecipe LWTBuildPondPump[\s\S]*item 1 Base\.Mov_LiveWater_PondPump")

    def test_sandbox_flow_multiplier(self):
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="ascii") as f:
            text = f.read()
        self.assertRegex(text, r"^VERSION = 1,")
        self.assertRegex(text, r"option LiveWater\.PumpFlowMultiplier\s*\{\s*type = double, min = [\d.]+, max = [\d.]+,"
                               r" default = 1\.0,\s*page = LiveWater, translation = LWT_PumpFlowMultiplier,")

    def test_texts_in_en_and_fr(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            def load(name):
                with open(os.path.join(tr, lang, name), encoding="utf-8") as f:
                    return json.load(f)
            ui, sandbox = load("IG_UI.json"), load("Sandbox.json")
            for key in ("IGUI_LWT_NoSource", "IGUI_LWT_Pump_Running", "IGUI_LWT_Pump_Standby", "IGUI_LWT_Pump_NoPower",
                        "IGUI_LWT_Pump_Flow", "IGUI_LWT_LW_Pumps", "IGUI_LWT_LW_Flow"):
                self.assertIn(key, ui, lang)
            for key in ("Sandbox_LiveWater", "Sandbox_LWT_PumpFlowMultiplier", "Sandbox_LWT_PumpFlowMultiplier_tooltip"):
                self.assertIn(key, sandbox, lang)
            self.assertIn("LWTBuildPondPump", load("Recipes.json"), lang)
            self.assertIn("Base.Mov_LiveWater_PondPump", load("ItemName.json"), lang)


if __name__ == "__main__":
    unittest.main()
