-- LiveWater: rules on the game objects that hold or give water (ADR-001 D18, D21, D28). Both sides:
-- the server adapters and the client menus ask the same rules.
--   RELAY_KEY, BARREL_KEY   ModData keys of LiveWater's relay tanks and connected barrels
--   WASHER_KEY              ModData key of a washer known plumbed (multiplayer fix, E28)
--   FOREIGN_KEYS            marks of other mods' objects never taken (Live Wire relays, barrels)
--   isFixture(obj)          a water fixture: its sprite carries the waterPiped flag
--   mark(obj, key)          ModData table under `key`, or nil
--   isBarrel(obj)           a barrel or rain collector LiveWater may connect: a FluidContainer of
--                           MIN_BARREL_LITRES or more, neither a fixture, nor a relay, nor marked
--                           by another mod
--   isWaterOnly(fc)         the container holds water (clean or tainted) only, or nothing
--   cityWaterRuns()         the city water still runs (rule of IsoObject.isWaterInfinite, 42.22)
--   cityInfo(obj)           what LWT_CityWater asks of a fixture

local WaterObjects = {}

WaterObjects.RELAY_KEY = "LiveWaterRelay"
WaterObjects.BARREL_KEY = "LiveWaterBarrel"
WaterObjects.WASHER_KEY = "LiveWaterWasher"
WaterObjects.FOREIGN_KEYS = { "LiveWireRelay", "LiveWireBarrel" }
WaterObjects.MIN_BARREL_LITRES = 20
WaterObjects.EPSILON = 0.001

function WaterObjects.isFixture(obj)
    if instanceof(obj, "IsoWorldInventoryObject") then return false end
    local sprite = obj:getSprite()
    local props = sprite and sprite:getProperties()
    return props ~= nil and props:has(IsoFlagType.waterPiped)
end

function WaterObjects.mark(obj, key)
    if not obj or not obj:hasModData() then return nil end
    local m = obj:getModData()[key]
    return type(m) == "table" and m or nil
end

local function foreign(obj)
    if not obj:hasModData() then return false end
    local md = obj:getModData()
    for i = 1, #WaterObjects.FOREIGN_KEYS do
        if md[WaterObjects.FOREIGN_KEYS[i]] ~= nil then return true end
    end
    return false
end

function WaterObjects.isBarrel(obj)
    if not obj or instanceof(obj, "IsoWorldInventoryObject") or WaterObjects.isFixture(obj) then return false end
    if obj:getUsesExternalWaterSource() or WaterObjects.mark(obj, WaterObjects.RELAY_KEY) or foreign(obj) then
        return false
    end
    local fc = obj:getFluidContainer()
    return fc ~= nil and fc:getCapacity() >= WaterObjects.MIN_BARREL_LITRES
end

function WaterObjects.isWaterOnly(fc)
    local amount = fc:getAmount()
    if amount <= WaterObjects.EPSILON then return true end
    local water = fc:getSpecificFluidAmount(Fluid.Water) + fc:getSpecificFluidAmount(Fluid.TaintedWater)
    return water >= amount - WaterObjects.EPSILON
end

function WaterObjects.cityWaterRuns()
    return getGameTime():getWorldAgeDaysSinceBegin() < getSandboxOptions():getWaterShutModifier()
end

function WaterObjects.cityInfo(obj)
    local sq = obj:getSquare()
    return { placed = obj:hasModData() and obj:getModData().canBeWaterPiped == true,
        plumbed = obj:getUsesExternalWaterSource(), room = sq ~= nil and sq:getRoom() ~= nil,
        noWater = sq ~= nil and sq:isNoWater() }
end

return WaterObjects
