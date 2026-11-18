if isClient() then return end
-- LiveWater: game adapter of the containers port of the barrel fittings (LWT_Fittings), authority
-- only (ADR-001 D26, P02). Thin: the rules are in LWT_Fittings, LWT_Flow and LWT_WaterObjects.
--   at(x, y, z)                     the container on the square: a vessel (LWT_WaterObjects.isVessel)
--                                   the fittings admit (LWT_Containers:admits: 20 L or more, or a
--                                   registered or listed name, E25), else a fuel pump of a gas
--                                   station (piped fuel, getPipedFuelAmount, Pump only); { fluid
--                                   ("clean", "tainted", "fuel", "other", nil when empty), amount,
--                                   free, sprite, entity } or nil
--   add(x, y, z, litres, quality)   litres poured in (Fluid.Water, TaintedWater or Petrol), sync
--   take(x, y, z, litres)           litres taken out (fluids kept in proportion), sync
-- Vanilla 42.22: FluidContainer getAmount, getFreeCapacity, getSpecificFluidAmount, addFluid,
-- removeFluid(float) (FluidContainer.java:493, 846, 880); IsoObject getPipedFuelAmount,
-- setPipedFuelAmount (IsoObject.java:2461, 2534).

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

local function entityName(obj)
    local script = obj:getEntityScript()
    return script and script:getName() or nil
end

-- The container object of a square and its kind ("fluid" or "fuel"), or nil.
function GameContainers:objectAt(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq then return nil end
    local objects, pump, listed = sq:getObjects(), nil, self.listed()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isVessel(obj)
            and self.registry:admits(obj:getFluidContainer():getCapacity(), obj:getSpriteName(), entityName(obj), listed) then
            return obj, "fluid"
        end
        if not pump and obj:getPipedFuelAmount() > 0 then pump = obj end
    end
    if pump then return pump, "fuel" end
    return nil
end

function GameContainers:at(x, y, z)
    local obj, kind = self:objectAt(x, y, z)
    if not obj then return nil end
    if kind == "fuel" then
        return { fluid = "fuel", amount = obj:getPipedFuelAmount(), free = 0, sprite = obj:getSpriteName() }
    end
    local fc = obj:getFluidContainer()
    return { fluid = fluidOf(fc), amount = fc:getAmount(), free = fc:getFreeCapacity(), sprite = obj:getSpriteName(),
        entity = entityName(obj) }
end

function GameContainers:add(x, y, z, litres, quality)
    local obj, kind = self:objectAt(x, y, z)
    local name = FLUIDS[quality]
    if not obj or kind ~= "fluid" or not name then return 0 end
    local fc = obj:getFluidContainer()
    local n = math.min(litres, fc:getFreeCapacity())
    if n <= 0 then return 0 end
    fc:addFluid(Fluid[name], n)
    obj:sync()
    return n
end

function GameContainers:take(x, y, z, litres)
    local obj, kind = self:objectAt(x, y, z)
    if not obj then return 0 end
    if kind == "fuel" then
        local left = obj:getPipedFuelAmount()
        local n = math.min(litres, left)
        -- whole units only: a fraction drawn takes a whole unit (rounded up), never creates fuel
        obj:setPipedFuelAmount(math.floor(left - n))
        return n
    end
    local fc = obj:getFluidContainer()
    local n = math.min(litres, fc:getAmount())
    if n <= 0 then return 0 end
    fc:removeFluid(n)
    obj:sync()
    return n
end

return GameContainers
