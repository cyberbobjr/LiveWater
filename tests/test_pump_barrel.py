"""ADR-011: the pond pump set down against a barrel (D01) pumps the barrel's water into the pipes (D02): water (and fuel since ADR-014), its
quality kept, never more than the barrel holds, shared with the other pumps against the same barrel; the barrel comes
before the pond (D03); its information shows the barrel (D04). Capability "vessel", intake field orVessel and
GameSite:hasVessel (API revision 21)."""
import json
import os
import unittest

from lwt_fakes import CONTAINERS, services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
FITTING = "shared/LiveWater/Parts/LWT_PartBarrelFitting.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"
LANGS = ("CN", "DE", "EN", "ES", "FR", "JP", "KO", "PT", "PTBR", "RU", "TR")

# Pump at (5,5) facing S, its barrel at (5,6), a pipe at (6,5) and a sprinkler at (7,5). The containers port behaves as
# the game: take never more than the barrel holds.
BENCH = CONTAINERS + r"""
function CONTAINERS:take(x, y, z, litres)
    local c = CONT[x .. "," .. y]
    local n = math.min(litres, c.amount)
    c.amount = c.amount - n
    return n
end
function CONTAINERS:add(x, y, z, litres, quality)
    local c = CONT[x .. "," .. y]
    local n = math.min(litres, c.capacity - c.amount)
    if n <= 0 then return 0 end
    c.amount = c.amount + n
    if c.fluid == nil or c.fluid == "clean" or quality ~= "clean" then c.fluid = quality end
    return n
end
LiveWater.API.registerPart("Test:Inlet", { sprites = { [0] = "t_inlet" },
    capabilities = { outlet = { type = "houseInlet" } } })
NEED = {}
FITTINGS = require("LiveWater/LWT_Fittings").new({ catalog = LiveWater.Parts, registry = REG, world = WORLD,
    containers = CONTAINERS, shapes = LiveWater.Containers })
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
OUTLETS:register("barrelFill", FITTINGS)
local need = { need = function(_, part) return NEED[part.x .. "," .. part.y] or 0 end, deliver = function() end }
OUTLETS:register("sprinkler", need)
OUTLETS:register("houseInlet", need)
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
LiveWater.Events.on("waterDrawn", function(part, litres) FITTINGS:drawn(part, litres) end)
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, sources = LiveWater.Sources,
    chores = { FITTINGS }, power = { powered = function() return true end },
    need = function(part) return OUTLETS:need(part) end })
function tick() EMITTED = {} CLOCK:tick() end
function againstBarrel(x, y) WORLD.dry[x .. "," .. y .. ",0"] = true WORLD.vessels[x .. "," .. y .. ",0"] = true end
function layout(outlet)
    againstBarrel(5, 5)
    assert(place("LiveWater:PondPump", 5, 5, "batman_livewater_01_24"))
    place("Test:Pipe", 6, 5)
    place(outlet or "Test:Spr", 7, 5)
    NEED["7,5"] = 20
end
function state(x, y) return REG:at(x, y, 0).data.outlet.state end
function delivered()
    local total, quality = 0, nil
    for _, e in ipairs(emitted("waterDelivered")) do total, quality = total + e[3], e[4] end
    return total, quality
end
"""


def bench():
    lua = services(new_lua, POND, FITTING)
    lua.execute(BENCH)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Siting(unittest.TestCase):
    def test_accepted_against_a_barrel_away_from_any_water(self):
        lua = bench()
        lua.execute("againstBarrel(5, 5)")
        self.assertTrue(lua.eval('place("LiveWater:PondPump", 5, 5)'))
        self.assertIsNone(lua.eval("REG:at(5, 5, 0).data.intake.source"))

    def test_refused_with_neither_water_nor_well_nor_barrel(self):
        lua = bench()
        lua.execute('WORLD.dry["5,5,0"] = true')
        self.assertEqual(call(lua, 'place("LiveWater:PondPump", 5, 5)'), (False, "no_source"))

    def test_next_to_natural_water_the_source_is_recorded_as_before(self):
        lua = bench()
        lua.execute('WORLD.vessels["0,0,0"] = true')
        self.assertTrue(lua.eval('place("LiveWater:PondPump", 0, 0)'))
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.intake.source"), "water")

    def test_a_part_without_or_vessel_still_needs_a_source(self):
        lua = bench()
        lua.execute("againstBarrel(5, 5)")
        self.assertEqual(call(lua, 'TOPO:canAdd("Test:Pump", 5, 5, 0)'), (False, "no_source"))


class PumpsTheBarrel(unittest.TestCase):
    def test_the_barrel_water_serves_the_outlet_and_leaves_the_barrel(self):
        lua = bench()
        lua.execute('layout() CONT["5,6"] = { amount = 100, capacity = 400, fluid = "clean" } tick()')
        self.assertEqual(lua.eval("delivered()")[0], 20)
        self.assertEqual(lua.eval("state(7, 5)"), "served")
        drawn = lua.eval('emitted("waterDrawn")')
        self.assertEqual(len(drawn), 1)
        self.assertEqual((drawn[1][2].x, drawn[1][2].y, drawn[1][3]), (5, 5, 20))
        self.assertEqual(lua.eval('CONT["5,6"].amount'), 80)

    def test_the_water_keeps_the_quality_of_the_barrel(self):
        lua = bench()
        lua.execute('layout() CONT["5,6"] = { amount = 100, capacity = 400, fluid = "clean" } tick()')
        self.assertEqual(lua.eval("delivered()")[1], "clean")
        lua = bench()
        lua.execute('layout() CONT["5,6"] = { amount = 100, capacity = 400, fluid = "tainted" } tick()')
        self.assertEqual(lua.eval("delivered()")[1], "tainted")

    def test_tainted_barrel_water_is_refused_by_a_house_without_filter(self):
        lua = bench()
        lua.execute('layout("Test:Inlet") CONT["5,6"] = { amount = 100, capacity = 400, fluid = "tainted" } tick()')
        self.assertEqual(lua.eval("state(7, 5)"), "unfiltered")
        self.assertEqual(lua.eval('CONT["5,6"].amount'), 100)

    def test_clean_barrel_water_reaches_the_house(self):
        lua = bench()
        lua.execute('layout("Test:Inlet") CONT["5,6"] = { amount = 100, capacity = 400, fluid = "clean" } tick()')
        self.assertEqual(lua.eval("state(7, 5)"), "served")

    def test_a_barrel_of_fuel_never_reaches_a_sprinkler(self):
        # ADR-014 D01: the pump draws fuel too; a sprinkler takes water only (D03)
        lua = bench()
        lua.execute('layout() CONT["5,6"] = { amount = 100, capacity = 400, fluid = "fuel" } tick()')
        self.assertEqual(lua.eval("state(7, 5)"), "wrong_fluid")
        self.assertEqual(lua.eval('CONT["5,6"].amount'), 100)
        self.assertEqual(len(lua.eval('emitted("waterDrawn")')), 0)

    def test_an_empty_barrel_gives_nothing(self):
        lua = bench()
        lua.execute('layout() CONT["5,6"] = { amount = 0, capacity = 400 } tick()')
        self.assertEqual(lua.eval("state(7, 5)"), "no_water")

    def test_no_barrel_any_more_gives_nothing(self):
        lua = bench()
        lua.execute("layout() tick()")
        self.assertEqual(lua.eval("state(7, 5)"), "no_water")


class BarrelBeforePond(unittest.TestCase):
    def test_the_barrel_first_then_the_pond_when_it_is_empty(self):
        lua = bench()
        lua.execute("""
        WORLD.vessels["5,5,0"] = true place("LiveWater:PondPump", 5, 5, "batman_livewater_01_24")
        place("Test:Pipe", 6, 5) place("Test:Spr", 7, 5) NEED["7,5"] = 20
        CONT["5,6"] = { amount = 30, capacity = 400, fluid = "clean" } tick()
        """)
        self.assertEqual(lua.eval("REG:at(5, 5, 0).data.intake.source"), "water")
        self.assertEqual(lua.eval("delivered()"), (20, "clean"))
        self.assertEqual(lua.eval('CONT["5,6"].amount'), 10)
        lua.execute('CONT["5,6"].amount = 0 tick()')
        self.assertEqual(lua.eval("delivered()"), (20, "tainted"))
        self.assertEqual(len(lua.eval('emitted("waterDrawn")')), 0)


class TwoPumps(unittest.TestCase):
    def test_a_pond_pump_never_draws_the_barrel_of_another_pump(self):
        lua = bench()
        lua.execute("""
        place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:Pipe", 1, 0)
        againstBarrel(2, 0) place("LiveWater:PondPump", 2, 0, "batman_livewater_01_24")
        CONT["2,-1"] = { amount = 100, capacity = 400, fluid = "clean" }
        place("Test:Spr", 1, 1) NEED["1,1"] = 200 tick()
        """)
        self.assertEqual(lua.eval("NET:networkAt(0, 0, 0)"), lua.eval("NET:networkAt(2, 0, 0)"))
        self.assertEqual(lua.eval("delivered()"), (100, "tainted"))
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 50)
        drawn = lua.eval('emitted("waterDrawn")')
        self.assertEqual(len(drawn), 1)
        self.assertEqual((drawn[1][2].x, drawn[1][3]), (2, 50))


class PumpAndFill(unittest.TestCase):
    def test_water_moves_from_the_pump_barrel_to_a_barrel_set_to_fill(self):
        lua = bench()
        lua.execute("""
        layout() NEED["7,5"] = 0
        CONT["5,6"] = { amount = 100, capacity = 400, fluid = "clean" }
        place("Test:Pipe", 6, 4) place("LiveWater:BarrelFitting", 6, 3, "batman_livewater_01_66")
        CONT["6,2"] = { amount = 0, capacity = 200 }
        tick()
        """)
        self.assertEqual(lua.eval('REG:at(6, 3, 0).data.fitting.cx'), 6)
        self.assertEqual((lua.eval('CONT["5,6"].amount'), lua.eval('CONT["6,2"].amount')), (50, 50))
        self.assertEqual(lua.eval('CONT["6,2"].fluid'), "tainted")

    def test_a_fill_on_the_pump_own_barrel_never_creates_water(self):
        for start in (190, 100):
            lua = bench()
            lua.execute("""
            layout() NEED["7,5"] = 0
            CONT["5,6"] = { amount = %d, capacity = 200, fluid = "clean" }
            place("LiveWater:BarrelFitting", 6, 6, "batman_livewater_01_66")
            """ % start)
            for _ in range(6):
                lua.execute("tick()")
                self.assertEqual(lua.eval('REG:at(6, 6, 0).data.fitting.cx'), 5)
                amount = lua.eval('CONT["5,6"].amount')
                self.assertLessEqual(amount, start + 1e-9, start)
                self.assertGreaterEqual(amount, start - 1e-9, start)


class Rate(unittest.TestCase):
    def test_the_draw_is_capped_at_the_rate(self):
        lua = bench()
        d = '{ type = "LiveWater:PondPump", data = { vessel = { found = true, fluid = "clean", amount = 300 } } }'
        self.assertEqual(call(lua, 'LiveWater.Parts:first(%s, "draw")' % d), (50, "clean"))

    def test_the_barrel_is_shared_with_another_pump_against_it(self):
        lua = bench()
        lua.execute("""
        layout() CONT["5,6"] = { amount = 100, capacity = 400, fluid = "clean" }
        againstBarrel(4, 6) place("LiveWater:PondPump", 4, 6, "batman_livewater_01_24")
        FITTINGS:tick()
        """)
        self.assertEqual(lua.eval("REG:at(4, 6, 0).data.vessel.cx"), 5)
        self.assertEqual(lua.eval("REG:at(5, 5, 0).data.vessel.share"), 50)
        self.assertEqual(lua.eval("REG:at(4, 6, 0).data.vessel.share"), 50)


class Information(unittest.TestCase):
    def lines(self, lua):
        return [(l[1], l[2]) for l in lua.eval("LiveWater.Parts:lines(REG:at(5, 5, 0))").values()]

    def test_the_barrel_and_its_content(self):
        lua = bench()
        lua.execute('layout() CONT["5,6"] = { amount = 79.6, capacity = 400, fluid = "clean" } FITTINGS:tick()')
        self.assertIn(("IGUI_LWT_Vessel_Content", 80), self.lines(lua))


class Capability(unittest.TestCase):
    def api(self):
        lua = new_lua(API)
        lua.execute("print = function() end")
        return lua

    def test_revision_21_or_later(self):
        self.assertGreaterEqual(self.api().eval("LiveWater.API.revision"), 21)

    def test_invalid_fields_are_refused(self):
        lua = self.api()
        for caps, field in (('vessel = { rate = -1 }', "vessel.rate"), ('vessel = { rate = "fast" }', "vessel.rate"),
                            ('intake = { orVessel = "yes" }', "intake.orVessel")):
            self.assertEqual(call(lua, 'LiveWater.Parts:register("Test:X", { sprites = { [0] = "x" },'
                                       ' capabilities = { %s } })' % caps), (False, "invalid_field"), field)


# Squares of GameSite: OBJ[x..","..y] = list of objects.
SITE = r"""
OBJ = {}
IsoFlagType = {}
function instanceof() return false end
function vessel(capacity, sprite, entity)
    local fc = { getCapacity = function() return capacity end }
    return { getSprite = function() return nil end, getUsesExternalWaterSource = function() return false end,
        hasModData = function() return false end, getFluidContainer = function() return fc end,
        getSpriteName = function() return sprite end,
        getEntityScript = function() return entity and { getName = function() return entity end } or nil end }
end
-- A gas station fuel pump: its sprite carries the property "fuelAmount" (IsoPropertyType.FUEL_AMOUNT, Java 42.22).
function gasPump()
    local props = { has = function(_, name) return name == "fuelAmount" end }
    return { getSprite = function() return { getProperties = function() return props end } end,
        getUsesExternalWaterSource = function() return false end,
        hasModData = function() return false end, getFluidContainer = function() return nil end,
        getSpriteName = function() return "location_shop_gas_01_0" end, getPipedFuelAmount = function() return 100 end }
end
function getCell() return { getGridSquare = function(_, x, y, z)
    local objs = OBJ[x .. "," .. y] or {}
    return { has = function() return false end,
        getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
end } end
GameSite = require("LiveWater/LWT_GameSite")
LISTED = {}
function site() return GameSite.new(LiveWater.Sources, 0, 0, 0,
    { registry = LiveWater.Containers, listed = function() return LISTED end }) end
"""


class Site(unittest.TestCase):
    def site(self):
        lua = new_lua(API)
        lua.execute(SITE)
        return lua

    def test_a_barrel_on_one_of_the_four_sides(self):
        lua = self.site()
        self.assertFalse(lua.eval("site():hasVessel()"))
        lua.execute('OBJ["0,1"] = { vessel(200, "carpentry_02_122") }')
        self.assertTrue(lua.eval("site():hasVessel()"))

    def test_a_diagonal_barrel_does_not_count(self):
        lua = self.site()
        lua.execute('OBJ["1,1"] = { vessel(200, "carpentry_02_122") }')
        self.assertFalse(lua.eval("site():hasVessel()"))

    def test_small_containers_only_when_registered_or_listed(self):
        lua = self.site()
        lua.execute('OBJ["-1,0"] = { vessel(5, "my_pot_0") }')
        self.assertFalse(lua.eval("site():hasVessel()"))
        lua.execute('LISTED = { my_pot_0 = true }')
        self.assertTrue(lua.eval("site():hasVessel()"))
        lua.execute('OBJ["-1,0"] = { vessel(15, "x", "WaterDispenser") }')
        self.assertTrue(lua.eval("site():hasVessel()"))

    def test_a_site_without_containers_has_no_barrel(self):
        lua = self.site()
        lua.execute('OBJ["0,1"] = { vessel(200, "carpentry_02_122") }')
        self.assertFalse(lua.eval("GameSite.new(LiveWater.Sources, 0, 0, 0):hasVessel()"))


class Texts(unittest.TestCase):
    def test_every_language_has_the_barrel_lines_and_the_refusal_names_the_barrel(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in LANGS:
            with open(os.path.join(tr, lang, "IG_UI.json"), encoding="utf-8") as f:
                ui = json.load(f)
            self.assertIn("IGUI_LWT_Vessel_Content", ui, lang)
            self.assertIn("%1", ui["IGUI_LWT_Vessel_Content"], lang)
        with open(os.path.join(tr, "FR", "IG_UI.json"), encoding="utf-8") as f:
            self.assertIn("un baril ou une pompe de station-service", json.load(f)["IGUI_LWT_NoSource"])
        with open(os.path.join(tr, "EN", "IG_UI.json"), encoding="utf-8") as f:
            self.assertIn("barrel", json.load(f)["IGUI_LWT_NoSource"])


if __name__ == "__main__":
    unittest.main()
