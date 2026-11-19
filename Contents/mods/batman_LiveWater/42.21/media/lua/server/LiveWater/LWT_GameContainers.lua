if isClient() then return end
-- LiveWater: game adapter of the containers port (LWT_Fittings: barrel fittings, pumps against a barrel),
-- authority only (ADR-001 D26, P02; ADR-011; ADR-013). Thin: the rules are in LWT_Fittings, LWT_Flow and
-- LWT_WaterObjects.
--   at(x, y, z)                     the container on the square: a vessel the fittings admit
--                                   (LWT_WaterObjects.isBarrel, LWT_Containers:admits: 20 L or more, or
--                                   a registered or listed name, E25), a vanilla feeding trough, or a
--                                   gas station fuel pump (LWT_WaterObjects.isFuelPump, ADR-014 D01);
--                                   { fluid ("clean", "tainted", "fuel", "other", nil when empty),
--                                   amount, free, sprite, entity, blocked ("feed": a trough holding feed
--                                   has no water tank, nothing goes in, ADR-013 D04), takes (what it
--                                   takes even empty: "water" for a trough, ADR-014 D04) } or nil
--   add(x, y, z, litres, quality)   litres poured in (Fluid.Water, TaintedWater or Petrol), sync
--   take(x, y, z, litres)           litres taken out (fluids kept in proportion), sync
-- A feeding trough (IsoFeedingTrough, Java 42.22) keeps its water tank on its master tile (getMasterTrough:
-- a fitting against any tile of a long trough fills it); water goes in and out through its own methods
-- (addWater: tank, water drawing and global object; removeWater then checkOverlayAfterAnimalEat), synced
-- with sendSyncEntity, as the vanilla trough commands do (server ClientCommands feedingThrough). It holds
-- water only. Vanilla 42.22: FluidContainer getAmount, getFreeCapacity, getSpecificFluidAmount, addFluid,
-- removeFluid(float) (FluidContainer.java:493, 846, 880).
-- A gas station fuel pump holds piped fuel, whole units (IsoObject getPipedFuelAmount, -1 while never read
-- without current; setPipedFuelAmount transmits its mod data itself, IsoObject.java:2461, 2534, as the
-- vanilla ISRefuelFromGasPump and ISTakeFuel rely on): it has no room (free 0, never filled) and what is
-- taken leaves it in whole units, rounded so that no fuel is ever created.

local WaterObjects = require "LiveWater/LWT_WaterObjects"

local GameContainers = {}
GameContainers.__index = GameContainers

local EPSILON = WaterObjects.EPSILON

-- Quality -> name of the fluid poured in.
local FLUIDS = { clean = "Water", tainted = "TaintedWater", fuel = "Petrol" }

-- deps: { registry (LWT_Containers), listed (function() -> set of the names of the sandbox option) }.
function GameContainers.new(deps)
    return setmetatable({ registry = deps.registry, listed = deps.listed }, GameContainers)
end

local function squareAt(x, y, z)
    local cell = getCell()
    return cell and cell:getGridSquare(x, y, z) or nil
end

local function fluidOf(fc)
    local amount = fc:getAmount()
    if amount <= EPSILON then return nil end
    if fc:getSpecificFluidAmount(Fluid.Petrol) >= amount - EPSILON then return "fuel" end
    local tainted = fc:getSpecificFluidAmount(Fluid.TaintedWater)
    if fc:getSpecificFluidAmount(Fluid.Water) + tainted >= amount - EPSILON then
        return tainted > EPSILON and "tainted" or "clean"
    end
    return "other"
end

-- How a container object is read and how litres go in and out of it, by kind.
local KINDS
KINDS = {
    vessel = {
        at = function(obj)
            local fc = obj:getFluidContainer()
            return { fluid = fluidOf(fc), amount = fc:getAmount(), free = fc:getFreeCapacity(),
                sprite = obj:getSpriteName(), entity = WaterObjects.entityName(obj) }
        end,
        add = function(obj, name, n)
            obj:getFluidContainer():addFluid(Fluid[name], n)
            obj:sync()
            return n
        end,
        take = function(obj, n)
            obj:getFluidContainer():removeFluid(n)
            obj:sync()
        end,
    },
    trough = {
        at = function(obj)
            if not obj:getFluidContainer() then
                return { blocked = "feed", amount = 0, free = 0, sprite = obj:getSpriteName(), takes = "water" }
            end
            local c = KINDS.vessel.at(obj)
            c.takes = "water"
            return c
        end,
        add = function(obj, name, n)
            if name ~= "Water" and name ~= "TaintedWater" then return 0 end
            obj:addWater(FluidType[name], n)
            obj:sendSyncEntity(nil)
            return n
        end,
        take = function(obj, n)
            obj:removeWater(n)
            obj:sendSyncEntity(nil)
            obj:checkOverlayAfterAnimalEat()
        end,
    },
    fuelPump = {
        at = function(obj)
            return { fluid = "fuel", amount = math.max(0, obj:getPipedFuelAmount()), free = 0,
                sprite = obj:getSpriteName() }
        end,
        add = function()
            return 0
        end,
        take = function(obj, n)
            obj:setPipedFuelAmount(math.floor(math.max(0, obj:getPipedFuelAmount()) - n))
        end,
    },
}

-- The container object of a square and its kind ("vessel", "trough" or "fuelPump"), or nil; a barrel
-- comes before a fuel pump on the same square.
function GameContainers:objectAt(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq then return nil end
    local objects, listed, pump = sq:getObjects(), self.listed(), nil
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if instanceof(obj, "IsoFeedingTrough") then return obj:getMasterTrough() or obj, "trough" end
        if WaterObjects.isBarrel(obj, self.registry, listed) then return obj, "vessel" end
        if not pump and WaterObjects.isFuelPump(obj) then pump = obj end
    end
    if pump then return pump, "fuelPump" end
    return nil
end

function GameContainers:at(x, y, z)
    local obj, kind = self:objectAt(x, y, z)
    if not obj then return nil end
    return KINDS[kind].at(obj)
end

function GameContainers:add(x, y, z, litres, quality)
    local obj, kind = self:objectAt(x, y, z)
    local name = FLUIDS[quality]
    if not obj or not name then return 0 end
    local n = math.min(litres, KINDS[kind].at(obj).free)
    if n <= 0 then return 0 end
    return KINDS[kind].add(obj, name, n)
end

function GameContainers:take(x, y, z, litres)
    local obj, kind = self:objectAt(x, y, z)
    if not obj then return 0 end
    local n = math.min(litres, KINDS[kind].at(obj).amount)
    if n <= 0 then return 0 end
    KINDS[kind].take(obj, n)
    return n
end

return GameContainers
