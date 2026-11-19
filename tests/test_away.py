"""ADR-006 D06-D08 (plan-006 V04): the networks keep working while no player is near. Every network with a part where
water starts is stepped at each ten-minute step, loaded or not; its pond pump draws on the source recorded when it
was set down; a crop is watered through its vanilla global object (SFarmingSystem, no square needed); a barrel
fitting on an unloaded square counts the content its last sense recorded, never below 0 nor above the room, and the
real container receives that count once when its chunk loads again; the house inlet takes nothing while unloaded;
current while unloaded: Live Wire's grid (gridAt) with the last circuit state known, else the public grid's global
state, else the last loaded generator state; back on a loaded square the normal rules resume."""
import unittest

from lwt_fakes import CONTAINERS, services
from lwt_harness import new_lua

POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
SPRINKLER = "shared/LiveWater/Parts/LWT_PartSprinkler.lua"
FITTING = "shared/LiveWater/Parts/LWT_PartBarrelFitting.lua"
FARMING = "server/LiveWater/LWT_GameFarming.lua"
TILE = "batman_livewater_01_"

# Vanilla farming double (media/lua/server/Farming 42.22): the global object system knows every plant, loaded or not;
# SPlantGlobalObject:water adds 10 per use up to 100, notes the hour and saves (the iso object only when loaded).
GLOBAL_PLANTS = r"""
SPlant = {}
SPlant.__index = SPlant
function SPlant:isAlive() return self.state ~= "dead" end
function SPlant:getIsoObject() return self.loaded and self.iso or nil end
function SPlant:water(source, uses)
    for i = 1, uses do
        if self.waterLvl < 100 then self.waterLvl = math.min(100, self.waterLvl + 10) end
    end
    self.lastWaterHour = SFarmingSystem.instance.hoursElapsed
    self:saveData()
end
function SPlant:saveData()
    local iso = self:getIsoObject()
    if iso then iso.waterLvl = self.waterLvl end
    self.saved = (self.saved or 0) + 1
end
SFarmingSystem = { instance = { hoursElapsed = 42, plants = {} } }
function SFarmingSystem.instance:getLuaObjectAt(x, y, z) return self.plants[x .. "," .. y .. "," .. z] end
function cropAt(x, y, level, needed)
    local p = setmetatable({ state = "seedInGround", waterLvl = level, waterNeeded = needed, iso = {}, loaded = false },
        SPlant)
    SFarmingSystem.instance.plants[x .. "," .. y .. ",0"] = p
    return p
end
"""

PLANTS_BENCH = GLOBAL_PLANTS + r"""
FARMING = require("LiveWater/LWT_GameFarming").new()
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
OUTLETS:register("sprinkler", require("LiveWater/LWT_Plants").new({ farming = FARMING,
    area = require("LiveWater/LWT_SprayArea").reach(LiveWater.Parts, function() return nil end) }))
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, publisher = PUB, sources = LiveWater.Sources,
    power = { powered = function() return true end }, need = function(part) return OUTLETS:need(part) end })
place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24")
place("Test:Pipe", 1, 0)
place("LiveWater:Sprinkler", 2, 0, "batman_livewater_01_48")
LiveWater.Parts:call(REG:at(2, 0, 0), "open", true)
function unloadAll()
    for x = -3, 5 do for y = -3, 3 do WORLD.unloaded[x .. "," .. y .. ",0"] = true end end
end
function tick() EMITTED = {} CLOCK:tick() end
"""


class Plants(unittest.TestCase):
    def bench(self):
        lua = services(new_lua, POND, SPRINKLER, FARMING)
        lua.execute(PLANTS_BENCH)
        return lua

    def test_an_unloaded_network_waters_a_crop_through_its_global_object_and_draws_its_flow(self):
        lua = self.bench()
        lua.execute("CROP = cropAt(3, 1, 0, 40) unloadAll() WORLD.sets = 0 WORLD.writes = 0 tick()")
        delivered = lua.eval('emitted("waterDelivered")')
        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[1][3], 10)
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.pump.litres"), 10)
        # 10 L less a quarter lost = 7.5 L = 37 doses of 0.2 L; the crop needs 4 (0 -> 40)
        self.assertEqual(lua.eval("CROP.waterLvl"), 40)
        self.assertEqual(lua.eval("CROP.lastWaterHour"), 42)
        self.assertEqual(lua.eval("CROP.saved"), 1)
        self.assertIsNone(lua.eval("CROP.iso.waterLvl"))
        self.assertEqual(lua.eval("REG:at(2, 0, 0).data.outlet.state"), "served")
        # no world write for unloaded parts: sprites and mirrored states wait for the return
        self.assertEqual(lua.eval("WORLD.sets"), 0)
        self.assertEqual(lua.eval("WORLD.writes"), 0)

    def test_the_parts_show_their_state_when_their_chunk_loads_again(self):
        lua = self.bench()
        lua.execute("CROP = cropAt(3, 1, 0, 40) unloadAll() tick()")
        # fed from the W: facing W (offset 3), off 48 + 3, on 52 + 3
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "51")
        lua.execute("WORLD.unloaded = {} PUB:chunkLoaded(0, 0, 8)")
        self.assertEqual(lua.eval("WORLD:sprite(2, 0, 0)"), TILE + "55")
        self.assertTrue(lua.eval('WORLD:stateOf(2, 0, 0, "LiveWater:Sprinkler").data.spray.on'))
        lua.execute("WORLD.writes = 0 PUB:chunkLoaded(0, 0, 8)")
        self.assertEqual(lua.eval("WORLD.writes"), 0)

    def test_a_network_without_any_part_where_water_starts_is_not_stepped(self):
        lua = self.bench()
        lua.execute('place("Test:Pipe", 20, 0) place("Test:Pipe", 21, 0)')
        stepped = lua.eval("CLOCK:tick()")
        self.assertEqual(len(stepped), 1)


# Containers port double that answers nothing on an unloaded square, as LWT_GameContainers does (no square).
BARREL_BENCH = CONTAINERS + r"""
CALLS = { add = 0, take = 0 }
local at, add, take = CONTAINERS.at, CONTAINERS.add, CONTAINERS.take
function CONTAINERS:at(x, y, z)
    if not WORLD:isLoaded(x, y, z) then return nil end
    return at(self, x, y, z)
end
function CONTAINERS:add(x, y, z, litres, quality)
    assert(WORLD:isLoaded(x, y, z), "add on an unloaded square")
    CALLS.add = CALLS.add + 1
    return add(self, x, y, z, litres, quality)
end
function CONTAINERS:take(x, y, z, litres)
    assert(WORLD:isLoaded(x, y, z), "take on an unloaded square")
    CALLS.take = CALLS.take + 1
    return take(self, x, y, z, litres)
end
NEED = {}
PUB = require("LiveWater/LWT_Publisher").new({ catalog = LiveWater.Parts, sprites = SPRITES, mirror = WORLD })
FITTINGS = require("LiveWater/LWT_Fittings").new({ catalog = LiveWater.Parts, registry = REG, world = WORLD,
    containers = CONTAINERS, shapes = LiveWater.Containers, publisher = PUB })
OUTLETS = require("LiveWater/LWT_Outlets").new(LiveWater.Parts)
OUTLETS:register("barrelFill", FITTINGS)
OUTLETS:register("sprinkler", { need = function(_, part) return NEED[part.x .. "," .. part.y] or 0 end,
    deliver = function() end })
LiveWater.Events.on("waterDelivered", function(part, litres, quality) OUTLETS:deliver(part, litres, quality) end)
LiveWater.Events.on("waterDrawn", function(part, litres) FITTINGS:drawn(part, litres) end)
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, publisher = PUB, chores = { FITTINGS },
    power = { powered = function() return true end }, need = function(part) return OUTLETS:need(part) end })
place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24")
place("Test:Pipe", 1, 0)
place("LiveWater:BarrelFitting", 2, 0, "batman_livewater_01_64")
FIT = REG:at(2, 0, 0)
function unloadAll()
    for x = -3, 5 do for y = -3, 3 do WORLD.unloaded[x .. "," .. y .. ",0"] = true end end
end
function tick() EMITTED = {} CLOCK:tick() end
function fitting() return REG:at(2, 0, 0).data.fitting end
function delivered()
    local d = emitted("waterDelivered")
    return d[1] and d[1][3] or 0, d[1] and d[1][4]
end
"""


class Barrels(unittest.TestCase):
    def bench(self):
        lua = services(new_lua, POND, FITTING)
        lua.execute(BARREL_BENCH)
        return lua

    def test_set_to_pump_an_unloaded_barrel_gives_its_recorded_content_never_below_zero(self):
        lua = self.bench()
        lua.execute(r"""
        place("Test:Spr", 1, 1) NEED["1,1"] = 20
        CONT["2,-1"] = { amount = 30, capacity = 600, fluid = "clean" }
        LiveWater.Parts:call(FIT, "setFittingMode", "pump")
        FITTINGS:tick()
        unloadAll()
        tick()
        """)
        self.assertEqual(tuple(lua.eval("{ delivered() }").values()), (20, "clean"))
        self.assertEqual(lua.eval("fitting().amount"), 10)
        lua.execute("tick()")
        self.assertEqual(tuple(lua.eval("{ delivered() }").values()), (10, "clean"))
        self.assertEqual(lua.eval("fitting().amount"), 0)
        lua.execute("tick()")
        # the barrel is empty: the pump is back on its own intake
        self.assertEqual(tuple(lua.eval("{ delivered() }").values()), (20, "tainted"))
        self.assertEqual(lua.eval("fitting().amount"), 0)
        self.assertEqual(lua.eval("fitting().free"), 600)
        # the real container was never touched while away
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 30)
        self.assertEqual(lua.eval("CALLS.take"), 0)

    def test_the_count_reaches_the_real_barrel_once_when_its_chunk_loads(self):
        lua = self.bench()
        lua.execute(r"""
        place("Test:Spr", 1, 1) NEED["1,1"] = 20
        CONT["2,-1"] = { amount = 30, capacity = 600, fluid = "clean" }
        LiveWater.Parts:call(FIT, "setFittingMode", "pump")
        FITTINGS:tick()
        unloadAll()
        tick()
        WORLD.unloaded = {}
        FITTINGS:chunkLoaded(0, -8, 8)
        FITTINGS:chunkLoaded(0, 0, 8)
        """)
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 10)
        self.assertEqual(lua.eval("CALLS.take"), 1)
        lua.execute("FITTINGS:chunkLoaded(0, 0, 8) NEED['1,1'] = 0 tick()")
        self.assertEqual(lua.eval("CALLS.take"), 1)
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 10)
        self.assertEqual(lua.eval("fitting().amount"), 10)

    def test_without_the_chunk_event_the_first_loaded_step_settles_the_count(self):
        lua = self.bench()
        lua.execute(r"""
        place("Test:Spr", 1, 1) NEED["1,1"] = 20
        CONT["2,-1"] = { amount = 30, capacity = 600, fluid = "clean" }
        LiveWater.Parts:call(FIT, "setFittingMode", "pump")
        FITTINGS:tick()
        unloadAll() tick()
        WORLD.unloaded = {} NEED["1,1"] = 0 tick()
        """)
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 10)
        self.assertEqual(lua.eval("CALLS.take"), 1)

    def test_set_to_fill_an_unloaded_barrel_takes_at_most_its_recorded_room(self):
        lua = self.bench()
        lua.execute(r"""
        CONT["2,-1"] = { amount = 380, capacity = 400, fluid = "tainted" }
        FITTINGS:tick()
        unloadAll()
        tick()
        """)
        self.assertEqual(lua.eval("(delivered())"), 20)
        self.assertEqual((lua.eval("fitting().amount"), lua.eval("fitting().free")), (400, 0))
        lua.execute("tick()")
        self.assertEqual(lua.eval("(delivered())"), 0)
        self.assertEqual(lua.eval("fitting().state"), "idle")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 380)
        self.assertEqual(lua.eval("CALLS.add"), 0)
        lua.execute("WORLD.unloaded = {} FITTINGS:chunkLoaded(0, -8, 8)")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 400)
        self.assertEqual(lua.eval('CONT["2,-1"].fluid'), "tainted")
        self.assertEqual(lua.eval("CALLS.add"), 1)

    def test_an_empty_unloaded_barrel_set_to_fill_takes_the_water_tainted(self):
        lua = self.bench()
        lua.execute(r"""
        CONT["2,-1"] = { amount = 0, capacity = 400 }
        FITTINGS:tick()
        unloadAll()
        tick()
        """)
        self.assertEqual(lua.eval("(delivered())"), 50)
        self.assertEqual((lua.eval("fitting().amount"), lua.eval("fitting().fluid")), (50, "tainted"))


# Live Wire double: consumers registered from revision 6; gridAt (authority) answers the snapshot of the grid that
# powers a square, from Live Wire's registry only (works unloaded): GRID["x,y,z"] = snapshot or nil.
LIVEWIRE = r"""
GRID = {}
function fakeLiveWire(revision, withGrid)
    local api = { revision = revision,
        registerConsumer = function() return true end,
        consumerPowered = function(obj) return obj.lw == true end }
    if withGrid then api.gridAt = function(x, y, z) return GRID[x .. "," .. y .. "," .. z] end end
    return api
end
function inverter(on) return { name = "", inverter = { id = 1, model = "m", state = "on", cond = 100, maxW = 1000,
    powered = on } } end
POW = nil
function newPower(api)
    POW = require("LiveWater/LWT_Power").new({ catalog = LiveWater.Parts, world = WORLD })
    POW:register(api)
end
place("LiveWater:PondPump", 0, 0, "batman_livewater_01_24")
PART = REG:at(0, 0, 0)
function away() WORLD.unloaded["0,0,0"] = true end
function back() WORLD.unloaded["0,0,0"] = nil end
"""


class Power(unittest.TestCase):
    def bench(self, api="nil"):
        lua = services(new_lua, POND)
        lua.execute(LIVEWIRE)
        lua.execute("newPower(%s)" % api)
        return lua

    def test_live_wire_grid_powered_or_not_while_unloaded(self):
        lua = self.bench("fakeLiveWire(7, true)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute('away() GRID["0,0,0"] = inverter(true)')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute('GRID["0,0,0"] = inverter(false)')
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_a_circuit_cut_at_the_last_loaded_step_stays_cut(self):
        lua = self.bench("fakeLiveWire(7, true)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = false')
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute('away() GRID["0,0,0"] = inverter(true)')
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_without_a_live_wire_grid_the_vanilla_rules_of_the_absence_apply(self):
        lua = self.bench("fakeLiveWire(7, true)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute("away()")
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute("WORLD.gridOff = true")
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_live_wire_without_grid_at_falls_back_to_the_vanilla_rules(self):
        lua = self.bench("fakeLiveWire(6, false)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute("away()")
        self.assertTrue(lua.eval("POW:powered(PART)"))

    def test_the_public_grid_follows_the_global_state_of_the_world(self):
        lua = self.bench()
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute("away()")
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute("WORLD.gridOff = true")
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_a_square_without_grid_power_stays_without_it(self):
        lua = self.bench()
        lua.execute('WORLD.unpowered["0,0,0"] = true')
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute("away()")
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_a_generator_keeps_the_state_of_the_last_loaded_step(self):
        lua = self.bench()
        lua.execute('WORLD.gridOff = true WORLD.generators["0,0,0"] = true')
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute("away() WORLD.generators = {}")
        self.assertTrue(lua.eval("POW:powered(PART)"))
        lua.execute('back()')
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute("away()")
        self.assertFalse(lua.eval("POW:powered(PART)"))

    def test_back_on_a_loaded_square_the_normal_reading_resumes(self):
        lua = self.bench("fakeLiveWire(7, true)")
        lua.execute('WORLD:object(0, 0, 0, "LiveWater:PondPump").lw = true away() GRID["0,0,0"] = inverter(false)')
        self.assertFalse(lua.eval("POW:powered(PART)"))
        lua.execute("back()")
        self.assertTrue(lua.eval("POW:powered(PART)"))

    def test_the_clock_tells_an_unloaded_pump_its_current(self):
        lua = self.bench()
        lua.execute(r"""
        CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
            catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, power = POW })
        place("Test:Spr", 1, 0)
        away() WORLD.gridOff = true CLOCK:tick()
        """)
        self.assertFalse(lua.eval("PART.data.pump.powered"))


if __name__ == "__main__":
    unittest.main()
