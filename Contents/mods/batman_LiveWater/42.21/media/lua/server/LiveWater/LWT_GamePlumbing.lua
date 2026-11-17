if isClient() then return end
-- LiveWater: game adapter of the plumbing port, authority only (ADR-001 D18, D21, D28). Thin: the
-- decisions are in LWT_InletArea, LWT_RelayPlan, LWT_Reserve, LWT_Relays and LWT_HouseBarrels;
-- the object rules in LWT_WaterObjects.
--   building(x, y, z)          map building touching the square (the square or the 4 around), not
--                              one the players built: { x1, y1, x2, y2, minLevel, maxLevel,
--                              contains(self, x, y, z) } (BuildingDef, Java 42.22), or nil
--   fixtures(area)             water fixtures (sprite flag waterPiped) of the area that use, or may
--                              use, an outside source: plumbed (getUsesExternalWaterSource), set
--                              down by a player (ModData canBeWaterPiped) or after the city water
--                              shut-off; { x, y, z, source } (source: see LWT_RelayPlan)
--   relay(x, y, z)             our relay on the square: { owner, amount, free, feeds, why }, or nil
--                              (feeds: a plumbed fixture below draws from it)
--   placeRelay(x, y, z, owner, litres)   invisible tank (IsoThumpable + FluidContainer)
--   removeRelay(x, y, z, owner)          true when done or nothing to do, false when not loaded
--   fillRelay(x, y, z, litres, quality)  litres added (clean water, or tainted water)
--   markRelay(x, y, z, why)    note the reason the relay stays empty (diagnostic, L09)
--   barrel(x, y, z)            barrel on the square (LWT_WaterObjects.isBarrel): { amount, capacity,
--                              waterOnly, mark }, and whether the square is loaded
--   markBarrel(x, y, z, mark)  write (nil: clear) its LiveWaterBarrel mark, sent to the clients
--   transfer(bx, by, bz, rx, ry, rz, litres)  barrel -> relay, fluids kept in proportion
--                              (FluidContainer.Transfer); litres moved
-- Never touches an object marked by another mod (Live Wire relays and barrels, D21).

local WaterObjects = require "LiveWater/LWT_WaterObjects"

local GamePlumbing = {}
GamePlumbing.__index = GamePlumbing

GamePlumbing.RELAY_KEY = WaterObjects.RELAY_KEY
-- Reserved tile of the tileset, defined without an image (tuiles-contrat.md): invisible.
GamePlumbing.RELAY_SPRITE = "batman_livewater_01_76"

function GamePlumbing.new()
    return setmetatable({}, GamePlumbing)
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

local AROUND = { { 0, 0 }, { 0, -1 }, { 1, 0 }, { 0, 1 }, { -1, 0 } }

function GamePlumbing:building(x, y, z)
    for i = 1, #AROUND do
        local sq = squareAt(x + AROUND[i][1], y + AROUND[i][2], z)
        local b = sq and sq:getBuilding()
        local def = b and b:getDef()
        if def and not def:isUserDefined() then return wrapBuilding(def) end
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
                if sq and fixtureOn(sq) then
                    out[#out + 1] = { x = x, y = y, z = z, source = sourceOf(sq) }
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

-- A plumbed fixture on the floor below (its square or the 8 around) draws from this relay.
local function feeds(relay, x, y, z)
    for dx = -1, 1 do
        for dy = -1, 1 do
            local sq = squareAt(x + dx, y + dy, z - 1)
            if sq then
                local objects = sq:getObjects()
                for i = 0, objects:size() - 1 do
                    local obj = objects:get(i)
                    if WaterObjects.isFixture(obj) and obj:getUsesExternalWaterSource()
                        and IsoObject.FindExternalWaterSource(sq) == relay then
                        return true
                    end
                end
            end
        end
    end
    return false
end

function GamePlumbing:relay(x, y, z)
    local obj = relayObject(x, y, z)
    local fc = obj and obj:getFluidContainer()
    if not fc then return nil end
    local mark = markOf(obj)
    return { owner = mark.inlet, amount = fc:getAmount(), free = fc:getFreeCapacity(), feeds = feeds(obj, x, y, z),
        why = mark.why }
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
    relay:getModData()[GamePlumbing.RELAY_KEY] = { inlet = owner }
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

function GamePlumbing:markRelay(x, y, z, why)
    local obj = relayObject(x, y, z)
    local mark = markOf(obj)
    if not mark or mark.why == why then return end
    mark.why = why
    if isServer() then obj:transmitModData() end
end

local function barrelObject(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq then return nil, nil end
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isBarrel(obj) then return obj, sq end
    end
    return nil, sq
end

function GamePlumbing:barrel(x, y, z)
    local obj, sq = barrelObject(x, y, z)
    if not obj then return nil, sq ~= nil end
    local fc = obj:getFluidContainer()
    return { amount = fc:getAmount(), capacity = fc:getCapacity(), waterOnly = WaterObjects.isWaterOnly(fc),
        mark = WaterObjects.mark(obj, WaterObjects.BARREL_KEY) }, true
end

function GamePlumbing:markBarrel(x, y, z, mark)
    local obj = barrelObject(x, y, z)
    if not obj then return end
    obj:getModData()[WaterObjects.BARREL_KEY] = mark
    if isServer() then obj:transmitModData() end
end

function GamePlumbing:transfer(bx, by, bz, rx, ry, rz, litres)
    local barrel, relay = barrelObject(bx, by, bz), relayObject(rx, ry, rz)
    if not barrel or not relay then return 0 end
    local target = relay:getFluidContainer()
    local before = target:getAmount()
    FluidContainer.Transfer(barrel:getFluidContainer(), target, litres)
    local moved = target:getAmount() - before
    if moved > 0 then
        relay:sync()
        barrel:sync()
    end
    return moved
end

return GamePlumbing
