-- LiveWater: rules on the game objects that hold or give water (ADR-001 D18, D21, D28). Both sides:
-- the server adapters and the client menus ask the same rules.
--   RELAY_KEY               ModData key of LiveWater's relay tanks
--   RELAY_LITRES            capacity of a relay tank (LWT_Relays places them, menus show it)
--   WASHER_KEY              ModData key of a washer known plumbed (multiplayer fix, E28)
--   FOREIGN_KEYS            marks of other mods' objects never taken (Live Wire relays, barrels)
--   isFixture(obj)          a water fixture: its sprite carries the waterPiped flag
--   mark(obj, key)          ModData table under `key`, or nil
--   isVessel(obj)           an object holding a FluidContainer LiveWater may use: neither an item
--                           on the floor, nor a fixture, nor a relay, nor marked by another mod
--   entityName(obj)         name of the entity script of an object, or nil
--   isBarrel(obj, registry, listed)  a vessel the barrel fittings work with: registry:admits
--                           (LWT_Containers: 20 L or more, registered or listed in `listed`)
--   isFuelPump(obj)         a gas station fuel pump: its sprite carries the property "fuelAmount"
--                           (IsoPropertyType.FUEL_AMOUNT; its piped fuel is IsoObject.getPipedFuelAmount,
--                           Java 42.22), ADR-014 D01
--   changesSources(obj)     set down or taken, it may change which fixture has which tank above:
--                           a fixture, or a water tank that is not one of LiveWater's relays
--   cityWaterRuns()         the city water still runs (rule of IsoObject.isWaterInfinite, 42.22)
--   cityInfo(obj)           what LWT_CityWater asks of a fixture
--   plumbInfo(obj)          what LWT_Plumbing asks of a fixture (ADR-024)

local WaterObjects = {}

WaterObjects.RELAY_KEY = "LiveWaterRelay"
WaterObjects.WASHER_KEY = "LiveWaterWasher"
WaterObjects.FOREIGN_KEYS = { "LiveWireRelay", "LiveWireBarrel" }
WaterObjects.RELAY_LITRES = 25
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

function WaterObjects.isVessel(obj)
    if not obj or instanceof(obj, "IsoWorldInventoryObject") or WaterObjects.isFixture(obj) then return false end
    if obj:getUsesExternalWaterSource() or WaterObjects.mark(obj, WaterObjects.RELAY_KEY) or foreign(obj) then
        return false
    end
    return obj:getFluidContainer() ~= nil
end

function WaterObjects.entityName(obj)
    local script = obj:getEntityScript()
    return script and script:getName() or nil
end

function WaterObjects.isBarrel(obj, registry, listed)
    return WaterObjects.isVessel(obj)
        and registry:admits(obj:getFluidContainer():getCapacity(), obj:getSpriteName(), WaterObjects.entityName(obj), listed)
end

function WaterObjects.isFuelPump(obj)
    if not obj or instanceof(obj, "IsoWorldInventoryObject") then return false end
    local sprite = obj:getSprite()
    local props = sprite and sprite:getProperties()
    return props ~= nil and props:has("fuelAmount")
end

function WaterObjects.changesSources(obj)
    if not obj or instanceof(obj, "IsoWorldInventoryObject") then return false end
    if WaterObjects.isFixture(obj) then return true end
    return obj:getFluidContainer() ~= nil and WaterObjects.mark(obj, WaterObjects.RELAY_KEY) == nil
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

function WaterObjects.plumbInfo(obj)
    local sq = obj:getSquare()
    local below = sq and getCell():getGridSquare(sq:getX(), sq:getY(), sq:getZ() - 1)
    return { plumbed = obj:getUsesExternalWaterSource(), source = obj:FindExternalWaterSource() ~= nil,
        room = sq ~= nil and sq:isInARoom(), roomBelow = below ~= nil and below:isInARoom() }
end

return WaterObjects
