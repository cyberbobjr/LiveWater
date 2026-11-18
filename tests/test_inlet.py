"""E09: house water inlet (ADR-001 D17, D18, D21): part LiveWater:HouseInlet drawn filtered or unfiltered; the area it
serves (the map building it touches, a range, up to 3 floors above); invisible 25 L relay tanks one level above the
plumbed fixtures (ModData LiveWaterRelay), shared by neighbouring fixtures; a fixture fed by something else (a Live Wire
relay, a vanilla barrel) is left alone; the inlet's need is the litres missing in its relays, delivered water fills
them; unfiltered water fills nothing; the relays leave with the inlet."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
INLET = "shared/LiveWater/Parts/LWT_PartHouseInlet.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
TILE = "batman_livewater_01_"

# Test double of the plumbing port (LWT_GamePlumbing). Buildings are rectangles on levels; fixtures are plumbed water
# fixtures; OTHER[key] marks a water source that is not ours on a square (a Live Wire relay, a vanilla barrel).
FAKE_PLUMBING = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end
FakePlumbing = {}
FakePlumbing.__index = FakePlumbing
function FakePlumbing.new()
    return setmetatable({ buildings = {}, list = {}, other = {}, relays = {}, placed = 0, removed = 0,
        unloaded = {}, scans = 0, cityRuns = true }, FakePlumbing)
end
local function building(b)
    function b:contains(x, y, z)
        return x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2 and z >= self.minLevel
            and z <= self.maxLevel and not (self.holes or {})[k(x, y, z)]
    end
    return b
end
function FakePlumbing:addBuilding(b) table.insert(self.buildings, building(b)) return b end
function FakePlumbing:addFixture(x, y, z, plumbed)
    table.insert(self.list, { x = x, y = y, z = z, plumbed = plumbed ~= false })
end
function FakePlumbing:building(x, y, z)
    for _, d in ipairs({ { 0, 0 }, { 0, -1 }, { 1, 0 }, { 0, 1 }, { -1, 0 } }) do
        for _, b in ipairs(self.buildings) do
            if b:contains(x + d[1], y + d[2], z) then return b end
        end
    end
    return nil
end
-- What IsoObject.FindExternalWaterSource gives for a fixture: a source on the square above, else around it.
function FakePlumbing:sourceOf(x, y, z)
    local found
    for _, d in ipairs({ { 0, 0 }, { -1, -1 }, { 0, -1 }, { 1, -1 }, { -1, 0 }, { 1, 0 }, { -1, 1 }, { 0, 1 }, { 1, 1 } }) do
        local key = k(x + d[1], y + d[2], z + 1)
        local r = self.relays[key]
        if self.other[key] then return "other" end
        if r and not found then found = { owner = r.owner, x = x + d[1], y = y + d[2], z = z + 1 } end
    end
    return found
end
function FakePlumbing:fixtures(area)
    self.scans = self.scans + 1
    local out = {}
    for _, f in ipairs(self.list) do
        if area:contains(f.x, f.y, f.z) then
            table.insert(out, { x = f.x, y = f.y, z = f.z, source = self:sourceOf(f.x, f.y, f.z) })
        end
    end
    return out
end
function FakePlumbing:relay(x, y, z)
    local r = self.relays[k(x, y, z)]
    if not r then return nil end
    local feeds = false
    for _, f in ipairs(self.list) do
        local s = f.plumbed and math.abs(f.x - x) <= 1 and math.abs(f.y - y) <= 1 and f.z == z - 1
            and self:sourceOf(f.x, f.y, f.z)
        if type(s) == "table" and s.x == x and s.y == y then feeds = true end
    end
    return { owner = r.owner, amount = r.amount, free = r.capacity - r.amount, feeds = feeds, why = r.why }
end
function FakePlumbing:placeRelay(x, y, z, owner, litres)
    self.relays[k(x, y, z)] = { owner = owner, amount = 0, capacity = litres }
    self.placed = self.placed + 1
    return true
end
function FakePlumbing:removeRelay(x, y, z, owner)
    local key = k(x, y, z)
    if self.unloaded[key] then return false end
    local r = self.relays[key]
    if r and r.owner == owner then
        self.relays[key] = nil
        self.removed = self.removed + 1
    end
    return true
end
function FakePlumbing:fillRelay(x, y, z, litres)
    local r = self.relays[k(x, y, z)]
    local n = math.min(litres, r.capacity - r.amount)
    r.amount = r.amount + n
    return n
end
function FakePlumbing:cityWaterRuns() return self.cityRuns end
function FakePlumbing:markRelay(x, y, z, why)
    local r = self.relays[k(x, y, z)]
    if r then r.why = why end
end
"""

BENCH = FAKE_PLUMBING + r"""
PLUMB = FakePlumbing.new()
NOW = 0
SETTINGS = {}
STORE.relays = nil
RELAYS = require("LiveWater/LWT_Relays").new({ store = STORE, plumbing = PLUMB, world = WORLD,
    now = function() return NOW end, setting = function(name) return SETTINGS[name] end,
    catalog = LiveWater.Parts, registry = REG, log = function(m) table.insert(LOGS, m) end })
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
OUTLETS:register("houseInlet", RELAYS)
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, sources = LiveWater.Sources,
    power = { powered = function() return true end }, publisher = PUB, chores = { RELAYS },
    need = function(part) return OUTLETS:need(part) end })
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
LiveWater.Events.on("partRemoved", function(entry) OUTLETS:release(entry) end)
-- A house: x 0..9, y 10..19, levels 0..4; the inlet stands outside its north wall at (5, 9).
HOUSE = PLUMB:addBuilding({ x1 = 0, y1 = 10, x2 = 9, y2 = 19, minLevel = 0, maxLevel = 4 })
function relayAt(x, y, z) return PLUMB.relays[x .. "," .. y .. "," .. z] end
"""


def bench(*extra):
    lua = services(new_lua, INLET, POND, *extra)
    lua.execute(BENCH)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class HouseInletPart(unittest.TestCase):
    def test_definition_follows_the_tile_contract(self):
        lua = new_lua(API, INLET)
        d = lua.eval('LiveWater.API.part("LiveWater:HouseInlet")')
        for key, base in (("filtered", 40), ("unfiltered", 44)):
            self.assertEqual([d.variants[key][i] for i in range(1, 5)], [TILE + str(base + k) for k in range(4)], key)
        self.assertEqual(d.capabilities.outlet.type, "houseInlet")
        self.assertEqual((d.capabilities.outlet.pressureCost, d.capabilities.outlet.needsClean), (2, True))

    def test_the_inlet_looks_unfiltered_after_a_step_refused_for_unfiltered_water(self):
        lua = new_lua(API, INLET)
        self.assertEqual(lua.eval('LiveWater.Parts:look({ type = "LiveWater:HouseInlet", data = {} })'), "filtered")
        lua.execute('P = { type = "LiveWater:HouseInlet", data = {} }'
                    ' LiveWater.Parts:call(P, "stepped", { through = 0, outlet = "unfiltered" })')
        self.assertEqual(lua.eval('LiveWater.Parts:look(P)'), "unfiltered")
        self.assertEqual(lua.eval('LiveWater.Parts:lines(P)[1][1]'), "IGUI_LWT_Outlet_unfiltered")

    def test_a_sprinkler_outlet_has_no_filter_look(self):
        lua = new_lua(API)
        lua.execute('LiveWater.API.registerPart("Test:S", { variants = { on = { "s1" } },'
                    ' capabilities = { outlet = { type = "sprinkler" } } })')
        self.assertIsNone(lua.eval('LiveWater.Parts:look({ type = "Test:S", data = {} })'))

    def test_moveable_recipe_and_translations_exist(self):
        with open(os.path.join(MEDIA, "scripts", "LWT_moveables.txt"), encoding="utf-8") as f:
            self.assertIn("Mov_LiveWater_HouseInlet", f.read())
        with open(os.path.join(MEDIA, "scripts", "LWT_recipes.txt"), encoding="utf-8") as f:
            self.assertIn("LWTBuildHouseInlet", f.read())
        for lang in ("EN", "FR"):
            with open(os.path.join(MEDIA, "lua", "shared", "Translate", lang, "IG_UI.json"), encoding="utf-8") as f:
                keys = json.load(f)
            for state in ("served", "idle", "no_water", "unfiltered", "no_pressure", "closed"):
                self.assertIn("IGUI_LWT_Outlet_" + state, keys)


class Area(unittest.TestCase):
    def area(self, lua, x, y, z=0):
        lua.execute("A = require('LiveWater/LWT_InletArea').of(PLUMB, %d, %d, %d, { building = SETTINGS.InletRange or 20,"
                    " base = 12 })" % (x, y, z))

    def test_the_building_touched_up_to_three_floors_above(self):
        lua = bench()
        self.area(lua, 5, 9)
        self.assertEqual(lua.eval("A.mode"), "building")
        self.assertTrue(lua.eval("A:contains(5, 12, 0)"))
        self.assertTrue(lua.eval("A:contains(2, 18, 3)"))
        self.assertFalse(lua.eval("A:contains(2, 18, 4)"))
        self.assertFalse(lua.eval("A:contains(5, 8, 0)"))

    def test_the_range_limits_a_large_building(self):
        lua = bench()
        lua.execute("PLUMB:addBuilding({ x1 = 100, y1 = 100, x2 = 160, y2 = 110, minLevel = 0, maxLevel = 0 })")
        lua.execute("SETTINGS.InletRange = 10")
        self.area(lua, 99, 105)
        self.assertTrue(lua.eval("A:contains(108, 105, 0)"))
        self.assertFalse(lua.eval("A:contains(115, 105, 0)"))


class RelayPlan(unittest.TestCase):
    def plan(self, lua, fixtures):
        lua.execute("W = require('LiveWater/LWT_RelayPlan').wanted(%s, '5,9,0')" % fixtures)
        keys = lua.eval("(function() local t = {} for k in pairs(W) do t[#t + 1] = k end table.sort(t) return t end)()")
        return [keys[i] for i in range(1, len(keys) + 1)]

    def test_one_relay_above_a_fixture_shared_by_its_neighbours(self):
        lua = new_lua(API)
        self.assertEqual(self.plan(lua, "{ { x = 1, y = 1, z = 0 }, { x = 2, y = 1, z = 0 }, { x = 5, y = 5, z = 1 } }"),
                         ["1,1,1", "5,5,2"])

    def test_a_fixture_fed_by_something_else_is_left_alone(self):
        lua = new_lua(API)
        self.assertEqual(self.plan(lua, '{ { x = 1, y = 1, z = 0, source = "other" } }'), [])

    def test_our_relay_is_kept_and_another_inlet_relay_is_left(self):
        lua = new_lua(API)
        self.assertEqual(self.plan(lua, '{ { x = 1, y = 1, z = 0, source = { owner = "5,9,0", x = 2, y = 2, z = 1 } },'
                                        ' { x = 8, y = 8, z = 0, source = { owner = "50,9,0", x = 8, y = 8, z = 1 } } }'),
                         ["2,2,1"])


class Relays(unittest.TestCase):
    def test_relays_go_above_the_fixtures_of_the_building_and_leave_with_the_inlet(self):
        lua = bench()
        lua.execute("PLUMB:addFixture(2, 12, 0) PLUMB:addFixture(3, 12, 0) PLUMB:addFixture(4, 15, 2)"
                    " PLUMB:addFixture(30, 30, 0)")
        self.assertTrue(lua.eval('place("LiveWater:HouseInlet", 5, 9, "%s42")' % TILE))
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).owner"), "5,9,0")
        self.assertIsNone(lua.eval("relayAt(3, 12, 1)"))
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 25)
        self.assertIsNotNone(lua.eval("relayAt(4, 15, 3)"))
        self.assertIsNone(lua.eval("relayAt(30, 30, 1)"))
        lua.execute("TOPO:remove(5, 9, 0)")
        self.assertIsNone(lua.eval("next(PLUMB.relays)"))

    def test_a_live_wire_relay_is_never_touched(self):
        lua = bench()
        lua.execute('PLUMB:addFixture(2, 12, 0) PLUMB.relays["2,12,1"] = { owner = "LiveWireRelay", amount = 3, capacity = 25 }'
                    ' PLUMB.other["2,12,1"] = true')
        lua.execute('place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick() TOPO:remove(5, 9, 0)' % TILE)
        self.assertEqual(lua.eval('PLUMB.relays["2,12,1"].owner'), "LiveWireRelay")
        self.assertEqual(lua.eval("PLUMB.placed"), 0)

    def test_a_relay_on_an_unloaded_square_is_removed_once_loaded(self):
        lua = bench()
        lua.execute('PLUMB:addFixture(2, 12, 0) place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()' % TILE)
        lua.execute('PLUMB.unloaded["2,12,1"] = true TOPO:remove(5, 9, 0) CLOCK:tick()')
        self.assertIsNotNone(lua.eval("relayAt(2, 12, 1)"))
        lua.execute('PLUMB.unloaded["2,12,1"] = nil CLOCK:tick()')
        self.assertIsNone(lua.eval("relayAt(2, 12, 1)"))


class Survey(unittest.TestCase):
    """ADR-001 D10: the fixtures of an inlet are surveyed on events only, never on a timer."""

    def placed(self):
        lua = bench()
        lua.execute('place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()' % TILE)
        self.assertEqual(lua.eval("PLUMB.scans"), 1)
        return lua

    def test_no_survey_while_nothing_happens(self):
        lua = self.placed()
        lua.execute("for i = 1, 12 do NOW = NOW + 1 CLOCK:tick() end")
        self.assertEqual(lua.eval("PLUMB.scans"), 1)

    def test_a_fixture_set_down_in_the_area_is_surveyed_at_the_next_step_once(self):
        lua = self.placed()
        lua.execute("PLUMB:addFixture(2, 12, 0) RELAYS:touched(2, 12, 0) RELAYS:touched(3, 12, 0) CLOCK:tick()")
        self.assertEqual(lua.eval("PLUMB.scans"), 2)
        self.assertIsNotNone(lua.eval("relayAt(2, 12, 1)"))
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("PLUMB.scans"), 2)

    def test_an_object_far_from_every_inlet_surveys_nothing(self):
        lua = self.placed()
        lua.execute("RELAYS:touched(300, 300, 0) RELAYS:chunkLoaded(296, 296, 8) CLOCK:tick()")
        self.assertEqual(lua.eval("PLUMB.scans"), 1)

    def test_a_chunk_loaded_over_the_area_surveys_again(self):
        lua = self.placed()
        lua.execute("PLUMB:addFixture(2, 12, 0) RELAYS:chunkLoaded(0, 8, 8) CLOCK:tick()")
        self.assertEqual(lua.eval("PLUMB.scans"), 2)
        self.assertIsNotNone(lua.eval("relayAt(2, 12, 1)"))

    def test_an_inlet_loaded_again_is_surveyed_again(self):
        lua = self.placed()
        lua.execute('WORLD.unloaded["5,9,0"] = true CLOCK:tick()')
        lua.execute('PLUMB:addFixture(2, 12, 0) WORLD.unloaded["5,9,0"] = nil CLOCK:tick()')
        self.assertEqual(lua.eval("PLUMB.scans"), 2)
        self.assertIsNotNone(lua.eval("relayAt(2, 12, 1)"))

    def test_the_city_water_shut_off_surveys_again(self):
        lua = self.placed()
        lua.execute("PLUMB.cityRuns = false CLOCK:tick()")
        self.assertEqual(lua.eval("PLUMB.scans"), 2)
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("PLUMB.scans"), 2)


class Delivery(unittest.TestCase):
    def setup(self, lua, near_well=True):
        if near_well:
            lua.execute('WORLD.dry["0,9,0"] = true WORLD.near["0,9,0"] = { camping_01_16 = true }')
        lua.execute('PLUMB:addFixture(2, 12, 0) PLUMB:addFixture(6, 16, 0)'
                    ' place("LiveWater:PondPump", 0, 9, "%s24")' % TILE)
        for x in range(1, 5):
            lua.execute('place("Test:Pipe", %d, 9)' % x)
        lua.execute('place("LiveWater:HouseInlet", 5, 9, "%s42")' % TILE)

    def test_the_need_is_the_litres_missing_in_the_relays_that_feed_a_plumbed_fixture(self):
        lua = bench()
        self.setup(lua)
        lua.execute("RELAYS:refresh(REG:at(5, 9, 0))")
        self.assertEqual(lua.eval("OUTLETS:need(REG:at(5, 9, 0))"), 50)
        lua.execute('PLUMB.list[2].plumbed = false')
        self.assertEqual(lua.eval("OUTLETS:need(REG:at(5, 9, 0))"), 25)

    def test_clean_water_delivered_fills_the_relays(self):
        lua = bench()
        self.setup(lua)
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).amount + relayAt(6, 16, 1).amount"), 50)
        self.assertEqual(lua.eval("REG:at(5, 9, 0).data.outlet.state"), "served")
        self.assertEqual(lua.eval("WORLD:sprite(5, 9, 0)"), TILE + "42")

    def test_unfiltered_water_fills_nothing_and_the_inlet_says_so(self):
        lua = bench()
        self.setup(lua, near_well=False)
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).amount"), 0)
        self.assertEqual(lua.eval("REG:at(5, 9, 0).data.outlet.state"), "unfiltered")
        self.assertEqual(lua.eval("WORLD:sprite(5, 9, 0)"), TILE + "46")


if __name__ == "__main__":
    unittest.main()
