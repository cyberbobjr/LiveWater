if isClient() then return end
-- LiveWater: game adapter of the plumbing port, authority only (ADR-001 D18, D21, D28). Thin: the
-- decisions are in LWT_InletArea, LWT_RelayPlan and LWT_Relays;
-- the object rules in LWT_WaterObjects.
--   building(x, y, z)          map building touching the square (the square or the 4 around), not
--                              one the players built: { x1, y1, x2, y2, minLevel, maxLevel,
--                              contains(self, x, y, z) } (BuildingDef, Java 42.22), or nil
--   fixtures(area)             water fixtures (sprite flag waterPiped) of the area that use, or may
--                              use, an outside source: plumbed (getUsesExternalWaterSource), set
--                              down by a player (ModData canBeWaterPiped) or after the city water
--                              shut-off; { x, y, z, source, mapBuilding, plumbed, need } (source:
--                              see LWT_RelayPlan; mapBuilding: its square is in a map building;
--                              plumbed: getUsesExternalWaterSource; need: litres the providers
--                              of LWT_FixtureNeeds ask for it, or nil, ADR-022)
--   relay(x, y, z)             our relay on the square: { owner, amount, free, capacity, feeds, why },
--                              or nil (feeds: a plumbed fixture below draws from it)
--   placeRelay(x, y, z, owner, litres)   invisible tank (IsoThumpable + FluidContainer)
--   resizeRelay(x, y, z, litres)         new capacity, sent to the clients; a smaller one loses the
--                                        water above it (FluidContainer.setCapacity, ADR-022 D05)
--   removeRelay(x, y, z, owner)          true when done or nothing to do, false when not loaded
--   fillRelay(x, y, z, litres, quality)  litres added (clean water, or tainted water)
--   emptyRelay(x, y, z)        the relay's water is thrown away (a valve cut the house, ADR-010 D04)
--   markRelay(x, y, z, why)    note the reason the relay stays empty (diagnostic, L09)
--   cityWaterRuns()            the city water still runs
--   cityFixture(x, y, z)       LWT_WaterObjects.cityInfo of the fixture on the square, or nil
--   connectCity(x, y, z)       the fixture takes the state of an original one (M01): its ModData
--                              canBeWaterPiped goes, no outside source; sent to the clients
--   washers(x, y, z)           washing machines fed by our relay on the square: { x, y, z,
--                              activated, plain (IsoClothingWasher), marked (LiveWaterWasher) }
--   sendWasherState(x, y, z)   sendObjectChange(WASHER_STATE) of the washer (E28)
--   markWasher(x, y, z)        ModData LiveWaterWasher = { plumbed = true }, sent to the clients
--   GamePlumbing.plumbedFixture(obj)  x, y, z of a plumbed water fixture, else nil (ADR-018)
-- Never touches an object marked by another mod (Live Wire relays and barrels, D21).

local WaterObjects = require "LiveWater/LWT_WaterObjects"

local GamePlumbing = {}
GamePlumbing.__index = GamePlumbing

GamePlumbing.RELAY_KEY = WaterObjects.RELAY_KEY
-- Reserved tile of the tileset, defined without an image (tuiles-contrat.md): invisible.
GamePlumbing.RELAY_SPRITE = "batman_livewater_01_76"
GamePlumbing.WASHER_KEY = WaterObjects.WASHER_KEY

-- needs: registry of the fixture need providers (LWT_FixtureNeeds), optional.
function GamePlumbing.new(needs)
    return setmetatable({ needs = needs }, GamePlumbing)
end

-- Square of `obj` when it is a water fixture that uses an outside water source (plumbed), else nil
-- (probe of LWT_PlumbWatch, ADR-018 D01).
function GamePlumbing.plumbedFixture(obj)
    if not obj or not WaterObjects.isFixture(obj) or not obj:getUsesExternalWaterSource() then return nil end
    local sq = obj:getSquare()
    if not sq then return nil end
    return sq:getX(), sq:getY(), sq:getZ()
end

local function squareAt(x, y, z)
    local cell = getCell()
    return cell and cell:getGridSquare(x, y, z) or nil
end

local function mayUseSource(obj)
    if obj:getUsesExternalWaterSource() then return true end
    return obj:getModData().canBeWaterPiped == true or not WaterObjects.cityWaterRuns()
end

local function wrapBuilding(def)
    return {
        x1 = def:getX(), y1 = def:getY(), x2 = def:getX2(), y2 = def:getY2(),
        minLevel = def:getMinLevel(), maxLevel = def:getMaxLevel(),
        contains = function(_, x, y, z) return def:containsXYZ(x, y, z) end,
    }
end

-- The square belongs to a building of the map, not one the players built.
local function inMapBuilding(sq)
    local b = sq:getBuilding()
    local def = b and b:getDef()
    return def ~= nil and not def:isUserDefined()
end

local AROUND = { { 0, 0 }, { 0, -1 }, { 1, 0 }, { 0, 1 }, { -1, 0 } }

function GamePlumbing:building(x, y, z)
    for i = 1, #AROUND do
        local sq = squareAt(x + AROUND[i][1], y + AROUND[i][2], z)
        if sq and inMapBuilding(sq) then return wrapBuilding(sq:getBuilding():getDef()) end
    end
    return nil
end

local function markOf(obj)
    return WaterObjects.mark(obj, GamePlumbing.RELAY_KEY)
end

-- Source of a fixture's square, as LWT_RelayPlan reads it.
local function sourceOf(sq)
    local src = IsoObject.FindExternalWaterSource(sq)
    if not src then return nil end
    local mark = markOf(src)
    if not mark then return "other" end
    local ss = src:getSquare()
    return { owner = mark.inlet, x = ss:getX(), y = ss:getY(), z = ss:getZ() }
end

local function fixtureOn(sq)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isFixture(obj) and mayUseSource(obj) then return obj end
    end
    return nil
end

function GamePlumbing:fixtures(area)
    local out = {}
    for z = area.minZ, area.maxZ do
        for x = area.minX, area.maxX do
            for y = area.minY, area.maxY do
                local sq = area:contains(x, y, z) and squareAt(x, y, z)
                local obj = sq and fixtureOn(sq)
                if obj then
                    out[#out + 1] = { x = x, y = y, z = z, source = sourceOf(sq), mapBuilding = inMapBuilding(sq),
                        plumbed = obj:getUsesExternalWaterSource(), need = self.needs and self.needs:need(obj) or nil }
                end
            end
        end
    end
    return out
end

local function relayObject(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq then return nil, nil end
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if markOf(obj) then return obj, sq end
    end
    return nil, sq
end

-- Plumbed fixtures on the floor below (the relay's square and the 8 around) drawing from `relay`.
local function fedBy(relay, x, y, z)
    local out = {}
    for dx = -1, 1 do
        for dy = -1, 1 do
            local sq = squareAt(x + dx, y + dy, z - 1)
            if sq then
                local objects = sq:getObjects()
                for i = 0, objects:size() - 1 do
                    local obj = objects:get(i)
                    if WaterObjects.isFixture(obj) and obj:getUsesExternalWaterSource()
                        and IsoObject.FindExternalWaterSource(sq) == relay then
                        out[#out + 1] = obj
                    end
                end
            end
        end
    end
    return out
end

local function feeds(relay, x, y, z)
    return #fedBy(relay, x, y, z) > 0
end

function GamePlumbing:relay(x, y, z)
    local obj = relayObject(x, y, z)
    local fc = obj and obj:getFluidContainer()
    if not fc then return nil end
    local mark = markOf(obj)
    return { owner = mark.inlet, amount = fc:getAmount(), free = fc:getFreeCapacity(), capacity = fc:getCapacity(),
        feeds = feeds(obj, x, y, z), why = mark.why }
end

function GamePlumbing:resizeRelay(x, y, z, litres)
    local obj = relayObject(x, y, z)
    local fc = obj and obj:getFluidContainer()
    if not fc then return end
    fc:setCapacity(litres)
    obj:sync()
end

function GamePlumbing:placeRelay(x, y, z, owner, litres)
    local cell = getCell()
    local sq = cell:getGridSquare(x, y, z) or cell:createNewGridSquare(x, y, z, true)
    if not sq then return false end
    local relay = IsoThumpable.new(cell, sq, GamePlumbing.RELAY_SPRITE, false)
    relay:setIsThumpable(false)
    relay:setCanPassThrough(true)
    relay:setBlockAllTheSquare(false)
    relay:setIsDismantable(false)
    relay:setCanBarricade(false)
    local fc = ComponentType.FluidContainer:CreateComponent()
    fc:setCapacity(litres)
    fc:setContainerName(GamePlumbing.RELAY_KEY)
    GameEntityFactory.AddComponent(relay, true, fc)
    relay:getModData()[GamePlumbing.RELAY_KEY] = { v = 1, inlet = owner }
    sq:transmitAddObjectToSquare(relay, -1)
    return true
end

function GamePlumbing:removeRelay(x, y, z, owner)
    local obj, sq = relayObject(x, y, z)
    if not sq then return false end
    local mark = markOf(obj)
    if mark and mark.inlet == owner then sq:transmitRemoveItemFromSquare(obj) end
    return true
end

function GamePlumbing:fillRelay(x, y, z, litres, quality)
    local obj = relayObject(x, y, z)
    local fc = obj and obj:getFluidContainer()
    if not fc then return 0 end
    local n = math.min(litres, fc:getFreeCapacity())
    if n <= 0 then return 0 end
    fc:addFluid(quality == "tainted" and Fluid.TaintedWater or Fluid.Water, n)
    obj:sync()
    return n
end

function GamePlumbing:emptyRelay(x, y, z)
    local obj = relayObject(x, y, z)
    local fc = obj and obj:getFluidContainer()
    if not fc or fc:getAmount() <= 0 then return end
    fc:Empty()
    obj:sync()
end

function GamePlumbing:markRelay(x, y, z, why)
    local obj = relayObject(x, y, z)
    local mark = markOf(obj)
    if not mark or mark.why == why then return end
    mark.why = why
    if isServer() then obj:transmitModData() end
end

local function isWasher(obj)
    return instanceof(obj, "IsoClothingWasher") or instanceof(obj, "IsoCombinationWasherDryer")
end

function GamePlumbing:washers(x, y, z)
    local relay, out = relayObject(x, y, z), {}
    if not relay then return out end
    local fed = fedBy(relay, x, y, z)
    for i = 1, #fed do
        local obj = fed[i]
        if isWasher(obj) then
            local sq = obj:getSquare()
            out[#out + 1] = { x = sq:getX(), y = sq:getY(), z = sq:getZ(), activated = obj:isActivated(),
                plain = instanceof(obj, "IsoClothingWasher"),
                marked = WaterObjects.mark(obj, GamePlumbing.WASHER_KEY) ~= nil }
        end
    end
    return out
end

local function washerAt(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq then return nil end
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        if isWasher(objects:get(i)) then return objects:get(i) end
    end
    return nil
end

function GamePlumbing:sendWasherState(x, y, z)
    local obj = washerAt(x, y, z)
    if obj then obj:sendObjectChange(IsoObjectChange.WASHER_STATE) end
end

function GamePlumbing:markWasher(x, y, z)
    local obj = washerAt(x, y, z)
    if not obj then return end
    obj:getModData()[GamePlumbing.WASHER_KEY] = { v = 1, plumbed = true }
    obj:transmitModData()
end

function GamePlumbing:cityWaterRuns()
    return WaterObjects.cityWaterRuns()
end

local function fixtureObject(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq then return nil end
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isFixture(obj) then return obj end
    end
    return nil
end

function GamePlumbing:cityFixture(x, y, z)
    local obj = fixtureObject(x, y, z)
    return obj and WaterObjects.cityInfo(obj) or nil
end

function GamePlumbing:connectCity(x, y, z)
    local obj = fixtureObject(x, y, z)
    if not obj then return false end
    obj:getModData().canBeWaterPiped = nil
    obj:setUsesExternalWaterSource(false)
    if isServer() then obj:transmitModData() end
    return true
end

return GamePlumbing
