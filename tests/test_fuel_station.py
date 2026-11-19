"""ADR-014: a pond pump set down against a gas station fuel pump draws its gasoline (D01); one fluid family per network
zone and step, set by the first pump in placement order that gives something (D02); consumers say what they take
(capability outlet field `takes`, D03); the fill fitting never mixes, a feeding trough takes water only (D04). API
revision 23."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
from test_pump_barrel import BENCH as PUMP_BENCH, FITTING, POND, SITE

API = "shared/LiveWater/LWT_API.lua"
DRIP = "shared/LiveWater/Parts/LWT_PartDripLine.lua"
VALVE = "shared/LiveWater/Parts/LWT_PartValve.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
LANGS = ("CN", "DE", "EN", "ES", "FR", "JP", "KO", "PT", "PTBR", "RU", "TR")

# The containers port also tells what an empty container takes (CONT[..].takes: a trough, "water"). A station is a
# CONT entry holding fuel with no free room. TANK is a consumer of another mod (need 30); Test:FuelTank takes fuel,
# Test:AnyTank anything, Test:WaterTank says nothing (water only).
BENCH = PUMP_BENCH + r"""
local at = CONTAINERS.at
function CONTAINERS:at(x, y, z)
    local c = at(self, x, y, z)
    if c then c.takes = CONT[x .. "," .. y].takes end
    return c
end
OUTLETS:register("drip", { need = function(_, part) return NEED[part.x .. "," .. part.y] or 0 end, deliver = function() end })
TANK = { given = {} }
function TANK:need(part) return 30 end
function TANK:deliver(part, litres, quality) table.insert(self.given, { x = part.x, litres = litres, quality = quality }) end
OUTLETS:register("Test:Tank", TANK)
LiveWater.API.registerPart("Test:FuelTank", { sprites = { [0] = "t_fueltank" },
    capabilities = { outlet = { type = "Test:Tank", takes = "fuel" } } })
LiveWater.API.registerPart("Test:AnyTank", { sprites = { [0] = "t_anytank" },
    capabilities = { outlet = { type = "Test:Tank", takes = "any" } } })
LiveWater.API.registerPart("Test:WaterTank", { sprites = { [0] = "t_watertank" },
    capabilities = { outlet = { type = "Test:Tank" } } })
-- A pond pump at (x, y) against a gas station fuel pump at (cx, cy) holding `litres` of gasoline.
function station(x, y, cx, cy, litres)
    againstBarrel(x, y)
    CONT[cx .. "," .. cy] = { amount = litres or 200, capacity = litres or 200, fluid = "fuel" }
    return place("LiveWater:PondPump", x, y, "batman_livewater_01_24")
end
function given(x)
    local total, quality = 0, nil
    for _, g in ipairs(TANK.given) do if g.x == x then total, quality = total + g.litres, g.quality end end
    return total, quality
end
function pumpLines(x, y)
    local out = {}
    for _, l in ipairs(LiveWater.Parts:lines(REG:at(x, y, 0))) do out[#out + 1] = l[1] end
    return out
end
"""


def bench():
    lua = services(new_lua, POND, FITTING, DRIP, VALVE)
    lua.execute(BENCH)
    return lua


def fuel_line(lua, outlet, sprite=None):
    """Station pump at (0,0) (station at (0,-1)), a pipe at (1,0), `outlet` at (2,0) needing 20 L."""
    lua.execute('station(0, 0, 0, -1) place("Test:Pipe", 1, 0) place("%s", 2, 0%s) NEED["2,0"] = 20'
                % (outlet, ', "%s"' % sprite if sprite else ""))
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class PumpAgainstAStation(unittest.TestCase):
    def test_gasoline_fills_an_empty_barrel_and_leaves_the_station(self):
        lua = fuel_line(bench(), "LiveWater:BarrelFitting", "batman_livewater_01_64")
        lua.execute('CONT["2,-1"] = { amount = 0, capacity = 100 } tick()')
        self.assertEqual(lua.eval('REG:at(2, 0, 0).data.fitting.state'), "served")
        self.assertEqual((lua.eval('CONT["2,-1"].amount'), lua.eval('CONT["2,-1"].fluid')), (50, "fuel"))
        self.assertEqual(lua.eval('CONT["0,-1"].amount'), 150)

    def test_a_house_a_sprinkler_and_a_drip_line_take_no_gasoline(self):
        for outlet in ("Test:Inlet", "Test:Spr", "LiveWater:DripLine"):
            lua = fuel_line(bench(), outlet)
            lua.execute("tick()")
            self.assertEqual(lua.eval("state(2, 0)"), "wrong_fluid", outlet)
            self.assertEqual(lua.eval('CONT["0,-1"].amount'), 200, outlet)
            self.assertEqual(len(lua.eval('emitted("waterDrawn")')), 0, outlet)

    def test_a_trough_takes_no_gasoline_even_empty(self):
        lua = fuel_line(bench(), "LiveWater:BarrelFitting", "batman_livewater_01_64")
        lua.execute('CONT["2,-1"] = { amount = 0, capacity = 100, takes = "water" } tick()')
        self.assertEqual(lua.eval('REG:at(2, 0, 0).data.fitting.state'), "wrong_fluid")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 0)
        self.assertEqual(lua.eval('CONT["0,-1"].amount'), 200)

    def test_a_barrel_of_water_takes_no_gasoline(self):
        lua = fuel_line(bench(), "LiveWater:BarrelFitting", "batman_livewater_01_64")
        lua.execute('CONT["2,-1"] = { amount = 10, capacity = 100, fluid = "clean" } tick()')
        self.assertEqual(lua.eval('REG:at(2, 0, 0).data.fitting.state'), "wrong_fluid")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 10)

    def test_a_barrel_of_gasoline_takes_gasoline(self):
        lua = fuel_line(bench(), "LiveWater:BarrelFitting", "batman_livewater_01_64")
        lua.execute('CONT["2,-1"] = { amount = 10, capacity = 100, fluid = "fuel" } tick()')
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 60)

    def test_an_empty_station_gives_nothing(self):
        lua = fuel_line(bench(), "Test:AnyTank")
        lua.execute('CONT["0,-1"].amount = 0 tick()')
        self.assertEqual(lua.eval("state(2, 0)"), "no_water")


class OneFluidPerNetwork(unittest.TestCase):
    def test_the_first_pump_placed_sets_the_fluid_water_first(self):
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:Pipe", 1, 0)'
                    ' station(2, 0, 2, -1) place("Test:AnyTank", 1, 1) tick()')
        self.assertEqual(lua.eval("given(1)"), (30, "tainted"))
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 200)
        self.assertEqual(len(lua.eval('emitted("waterDrawn")')), 0)
        self.assertIn("IGUI_LWT_Pump_OtherFluid", lua.eval("pumpLines(2, 0)").values())
        self.assertNotIn("IGUI_LWT_Pump_OtherFluid", lua.eval("pumpLines(0, 0)").values())

    def test_the_first_pump_placed_sets_the_fluid_gasoline_first(self):
        lua = bench()
        lua.execute('station(2, 0, 2, -1) place("Test:Pipe", 1, 0)'
                    ' place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:AnyTank", 1, 1) tick()')
        self.assertEqual(lua.eval("given(1)"), (30, "fuel"))
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 170)
        self.assertIn("IGUI_LWT_Pump_OtherFluid", lua.eval("pumpLines(0, 0)").values())
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.pump.running"), False)

    def test_the_other_pump_goes_back_to_work_when_alone(self):
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:Pipe", 1, 0)'
                    ' station(2, 0, 2, -1) place("Test:AnyTank", 1, 1) tick()'
                    ' LiveWater.Parts:call(REG:at(0, 0, 0), "switch", false) tick()')
        self.assertEqual(lua.eval("given(1)"), (60, "fuel"))
        self.assertNotIn("IGUI_LWT_Pump_OtherFluid", lua.eval("pumpLines(2, 0)").values())

    def test_a_closed_valve_makes_two_zones_each_with_its_fluid(self):
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:Pipe", 1, 0)'
                    ' place("LiveWater:Valve", 2, 0, "batman_livewater_01_16") place("Test:Pipe", 3, 0)'
                    ' station(4, 0, 4, -1) place("Test:AnyTank", 1, 1) place("Test:AnyTank", 3, 1)'
                    ' LiveWater.Parts:call(REG:at(2, 0, 0), "open", false) tick()')
        self.assertEqual(lua.eval("given(1)"), (30, "tainted"))
        self.assertEqual(lua.eval("given(3)"), (30, "fuel"))
        self.assertEqual(lua.eval('CONT["4,-1"].amount'), 170)


class ConsumersSayWhatTheyTake(unittest.TestCase):
    def test_a_consumer_of_gasoline_gets_gasoline(self):
        lua = fuel_line(bench(), "Test:FuelTank")
        lua.execute("tick()")
        self.assertEqual(lua.eval("given(2)"), (30, "fuel"))
        self.assertEqual(lua.eval('CONT["0,-1"].amount'), 170)

    def test_a_consumer_without_takes_gets_water_only(self):
        lua = fuel_line(bench(), "Test:WaterTank")
        lua.execute("tick()")
        self.assertEqual((lua.eval("state(2, 0)"), lua.eval("given(2)")[0]), ("wrong_fluid", 0))
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:WaterTank", 1, 0) tick()')
        self.assertEqual(lua.eval("given(1)"), (30, "tainted"))

    def test_a_consumer_of_gasoline_gets_no_water(self):
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:FuelTank", 1, 0) tick()')
        self.assertEqual(lua.eval("state(1, 0)"), "wrong_fluid")

    def test_livewater_consumers_take_water_explicitly(self):
        lua = bench()
        for t in ("Test:Inlet", "Test:Spr", "LiveWater:DripLine", "Test:WaterTank"):
            d = '{ type = "%s", data = {} }' % t
            self.assertEqual(lua.eval('select(4, LiveWater.Parts:first(%s, "outlet"))' % d), "water", t)
        self.assertEqual(lua.eval('select(4, LiveWater.Parts:first({ type = "Test:FuelTank", data = {} }, "outlet"))'),
                         "fuel")

    def test_a_bad_takes_is_refused(self):
        lua = new_lua(API)
        lua.execute("print = function() end")
        for value in ('"juice"', "1", "true"):
            self.assertEqual(call(lua, 'LiveWater.Parts:register("Test:X", { sprites = { [0] = "x" }, capabilities ='
                                       ' { outlet = { type = "Test:X", takes = %s } } })' % value),
                             (False, "invalid_field"), value)
        for value in ("water", "fuel", "other", "any"):
            self.assertTrue(lua.eval('LiveWater.Parts:register("Test:%s", { sprites = { [0] = "x%s" }, capabilities ='
                                     ' { outlet = { type = "Test:X", takes = "%s" } } })' % (value, value, value)))

    def test_revision_23(self):
        lua = new_lua(API)
        self.assertEqual(lua.eval("LiveWater.API.revision"), 23)


class Information(unittest.TestCase):
    def lines(self, lua, x, y):
        return [l[1] for l in lua.eval("LiveWater.Parts:lines(REG:at(%d, %d, 0))" % (x, y)).values()]

    def test_the_station_and_its_gasoline(self):
        lua = fuel_line(bench(), "Test:AnyTank")
        lua.execute("FITTINGS:tick()")
        lines = [(l[1], l[2]) for l in lua.eval("LiveWater.Parts:lines(REG:at(0, 0, 0))").values()]
        self.assertIn(("IGUI_LWT_Vessel_Tank", 200), lines)
        self.assertIn(("IGUI_LWT_Fluid_fuel", None), lines)
        self.assertNotIn("IGUI_LWT_Vessel_Content", [l[0] for l in lines])

    def test_a_water_consumer_says_this_is_not_water(self):
        for outlet, key in (("Test:Inlet", "IGUI_LWT_Outlet_wrong_fluid"), ("Test:Spr", "IGUI_LWT_Sprinkler_wrong_fluid"),
                            ("LiveWater:DripLine", "IGUI_LWT_Drip_wrong_fluid")):
            lua = fuel_line(bench(), outlet)
            lua.execute("tick()")
            self.assertIn(key, self.lines(lua, 2, 0), outlet)

    def test_another_consumer_says_wrong_liquid(self):
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:FuelTank", 1, 0) tick()')
        self.assertIn("IGUI_LWT_Outlet_WrongLiquid", self.lines(lua, 1, 0))

    def test_a_fitting_on_water_says_this_is_not_water(self):
        lua = fuel_line(bench(), "LiveWater:BarrelFitting", "batman_livewater_01_64")
        lua.execute('CONT["2,-1"] = { amount = 0, capacity = 100, takes = "water" } tick()')
        self.assertIn("IGUI_LWT_Fitting_NotWater", self.lines(lua, 2, 0))

    def test_a_fitting_on_gasoline_receiving_water_says_another_fluid(self):
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24") place("Test:Pipe", 1, 0)'
                    ' place("LiveWater:BarrelFitting", 2, 0, "batman_livewater_01_64") NEED["2,0"] = 20'
                    ' CONT["2,-1"] = { amount = 10, capacity = 100, fluid = "fuel" } tick()')
        self.assertIn("IGUI_LWT_Fitting_wrong_fluid", self.lines(lua, 2, 0))


# A gas station fuel pump as the game has it: its sprite carries the property "fuelAmount", its piped fuel is read
# and written in whole units (IsoObject.getPipedFuelAmount / setPipedFuelAmount, Java 42.22; the setter transmits).
GAME = r"""
Fluid = { Water = "Water", TaintedWater = "TaintedWater", Petrol = "Petrol" }
IsoFlagType = { waterPiped = "waterPiped" }
OBJ = {}
SETS = {}
function instanceof() return false end
function station(units)
    local s = { units = units }
    local props = { has = function(_, name) return name == "fuelAmount" end }
    function s:getSprite() return { getProperties = function() return props end } end
    function s:getSpriteName() return "location_shop_gas_01_0" end
    function s:getUsesExternalWaterSource() return false end
    function s:hasModData() return false end
    function s:getFluidContainer() return nil end
    function s:getEntityScript() return nil end
    function s:getPipedFuelAmount() return self.units end
    function s:setPipedFuelAmount(n) SETS[#SETS + 1] = n self.units = math.max(0, n) end
    return s
end
function getCell() return { getGridSquare = function(_, x, y, z)
    local objs = OBJ[x .. "," .. y] or {}
    return { getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
end } end
GC = require("LiveWater/LWT_GameContainers").new({ registry = LiveWater.Containers, listed = function() return {} end })
"""


def game():
    lua = new_lua(API, "server/LiveWater/LWT_GameContainers.lua")
    lua.execute(GAME)
    return lua


class GameStation(unittest.TestCase):
    def test_a_station_holds_its_piped_gasoline_and_has_no_room(self):
        lua = game()
        lua.execute('OBJ["0,0"] = { station(120) }')
        c = lua.eval("GC:at(0, 0, 0)")
        self.assertEqual((c.fluid, c.amount, c.free), ("fuel", 120, 0))

    def test_an_unpowered_station_never_read_holds_nothing(self):
        lua = game()
        lua.execute('OBJ["0,0"] = { station(-1) }')
        self.assertEqual(lua.eval("GC:at(0, 0, 0).amount"), 0)

    def test_gasoline_taken_leaves_the_station_in_whole_units_never_created(self):
        lua = game()
        lua.execute('S = station(120) OBJ["0,0"] = { S }')
        self.assertEqual(lua.eval("GC:take(0, 0, 0, 30)"), 30)
        self.assertEqual(lua.eval("S.units"), 90)
        self.assertEqual(lua.eval("GC:take(0, 0, 0, 2.5)"), 2.5)
        self.assertEqual(lua.eval("S.units"), 87)
        self.assertEqual(lua.eval("GC:take(0, 0, 0, 500)"), 87)
        self.assertEqual(lua.eval("S.units"), 0)

    def test_nothing_is_ever_poured_into_a_station(self):
        lua = game()
        lua.execute('S = station(10) OBJ["0,0"] = { S }')
        self.assertEqual(lua.eval('GC:add(0, 0, 0, 30, "fuel")'), 0)
        self.assertEqual((lua.eval("S.units"), len(lua.eval("SETS"))), (10, 0))


class Site(unittest.TestCase):
    def test_a_pump_may_stand_against_a_gas_station_pump(self):
        lua = new_lua(API)
        lua.execute(SITE)
        lua.execute('OBJ["1,0"] = { gasPump() }')
        self.assertTrue(lua.eval("site():hasVessel()"))

    def test_a_diagonal_gas_station_pump_does_not_count(self):
        lua = new_lua(API)
        lua.execute(SITE)
        lua.execute('OBJ["1,1"] = { gasPump() }')
        self.assertFalse(lua.eval("site():hasVessel()"))


def load(lang):
    with open(os.path.join(MEDIA, "lua", "shared", "Translate", lang, "IG_UI.json"), encoding="utf-8") as f:
        return json.load(f)


class Texts(unittest.TestCase):
    KEYS = ("IGUI_LWT_Pump_OtherFluid", "IGUI_LWT_Outlet_WrongLiquid", "IGUI_LWT_Fitting_NotWater",
            "IGUI_LWT_Vessel_Tank", "IGUI_LWT_Outlet_wrong_fluid", "IGUI_LWT_Sprinkler_wrong_fluid",
            "IGUI_LWT_Drip_wrong_fluid", "IGUI_LWT_Fitting_wrong_fluid")

    def test_every_language_has_the_lines(self):
        for lang in LANGS:
            ui = load(lang)
            for key in self.KEYS:
                self.assertTrue(ui.get(key, "").strip(), (lang, key))
            self.assertIn("%1", ui["IGUI_LWT_Vessel_Tank"], lang)

    def test_french_texts(self):
        ui = load("FR")
        self.assertEqual(ui["IGUI_LWT_Pump_OtherFluid"], "Pompe : un autre liquide est dans les tuyaux")
        self.assertEqual(ui["IGUI_LWT_Why_wrong_fluid"], "un autre liquide que l'eau est dans les tuyaux")
        self.assertEqual(ui["IGUI_LWT_NoSource"], "Doit \u00eatre pos\u00e9e au bord d'une eau naturelle (lac, "
                         "\u00e9tang, rivi\u00e8re), contre un puits, un baril ou une pompe de station-service.")
        self.assertEqual(ui["IGUI_LWT_Outlet_WrongLiquid"], "Mauvais liquide")
        for key in ("IGUI_LWT_Outlet_wrong_fluid", "IGUI_LWT_Sprinkler_wrong_fluid", "IGUI_LWT_Drip_wrong_fluid",
                    "IGUI_LWT_Fitting_NotWater"):
            self.assertEqual(ui[key], "Ce n'est pas de l'eau", key)

    def test_english_texts(self):
        ui = load("EN")
        self.assertEqual(ui["IGUI_LWT_Pump_OtherFluid"], "Pump: another liquid is in the pipes")
        self.assertEqual(ui["IGUI_LWT_Why_wrong_fluid"], "a liquid other than water is in the pipes")
        self.assertIn("gas station pump", ui["IGUI_LWT_NoSource"])
        self.assertEqual(ui["IGUI_LWT_Outlet_WrongLiquid"], "Wrong liquid")
        self.assertEqual(ui["IGUI_LWT_Outlet_wrong_fluid"], "This is not water")


if __name__ == "__main__":
    unittest.main()
