if isClient() then return end
-- LiveWater: game adapter of the world port (squares and part objects), authority only. Thin:
-- every decision is in the services that use it (LWT_Sprites, LWT_Clock, commands).
--   isLoaded(x, y, z)                 square loaded (getCell():getGridSquare non-nil)
--   isFree(x, y, z)                   floor, no water, nothing solid, no tree
--   spriteOf(x, y, z, typeId)         sprite of the object of that part type on the square
--   setSprite(x, y, z, typeId, name)  setSpriteFromName + transmitUpdatedSpriteToClients
--   createPart(x, y, z, spriteName)   new tile object, sent to the clients
--   removePart(x, y, z, typeId)       remove the object of that part type, sent to the clients
--   object(x, y, z, typeId)           the object of that part type, or nil
--   site(x, y, z)                     the place, for Parts:attach (LWT_GameSite)
--   hasPower(x, y, z)                 vanilla rule for an appliance outdoors or indoors: a
--                                     generator in range or the public grid (PowerPolicy
--                                     ExteriorOK of ObjectAmbientEmitters, Java 42.22)
--   writeState(x, y, z, typeId, s)    mirror the state on the object and send it (LWT_Mirror)
--   stateOf(x, y, z, typeId)          state mirrored on the object, or nil
--   stateOfObject(obj)                state mirrored on a game object, or nil
-- The part type of an object is found by its sprite through the part catalog.

local GameSite = require "LiveWater/LWT_GameSite"
local Mirror = require "LiveWater/LWT_Mirror"

local GameWorld = {}
GameWorld.__index = GameWorld

function GameWorld.new(catalog, sources)
    return setmetatable({ catalog = catalog, sources = sources }, GameWorld)
end

local function squareAt(x, y, z)
    local cell = getCell()
    if not cell then return nil end
    return cell:getGridSquare(x, y, z)
end

function GameWorld:objectOf(square, typeId)
    local objects = square:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        local name = obj:getSpriteName()
        if name and self.catalog:typeOfSprite(name) == typeId then return obj end
    end
    return nil
end

function GameWorld:isLoaded(x, y, z)
    return squareAt(x, y, z) ~= nil
end

function GameWorld:isFree(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq or not sq:getFloor() then return false end
    return not (sq:has(IsoFlagType.water) or sq:isSolid() or sq:isSolidTrans() or sq:HasTree())
end

function GameWorld:spriteOf(x, y, z, typeId)
    local sq = squareAt(x, y, z)
    local obj = sq and self:objectOf(sq, typeId)
    return obj and obj:getSpriteName() or nil
end

function GameWorld:setSprite(x, y, z, typeId, name)
    local sq = squareAt(x, y, z)
    local obj = sq and self:objectOf(sq, typeId)
    if not obj then return false end
    obj:setSpriteFromName(name)
    obj:transmitUpdatedSpriteToClients()
    return true
end

function GameWorld:object(x, y, z, typeId)
    local sq = squareAt(x, y, z)
    return sq and self:objectOf(sq, typeId) or nil
end

function GameWorld:site(x, y, z)
    return GameSite.new(self.sources, x, y, z)
end

function GameWorld:hasPower(x, y, z)
    local sq = squareAt(x, y, z)
    return sq ~= nil and (sq:haveElectricity() or sq:hasGridPower())
end

function GameWorld:writeState(x, y, z, typeId, state)
    local obj = self:object(x, y, z, typeId)
    if not obj then return false end
    Mirror.write(obj, state)
    if isServer() then obj:transmitModData() end
    return true
end

function GameWorld:stateOf(x, y, z, typeId)
    local state = Mirror.read(self:object(x, y, z, typeId))
    if state and state.type == typeId then return state end
    return nil
end

function GameWorld:stateOfObject(obj)
    return Mirror.read(obj)
end

function GameWorld:createPart(x, y, z, spriteName)
    local sq = squareAt(x, y, z)
    if not sq then return false end
    sq:transmitAddObjectToSquare(IsoObject.new(getCell(), sq, spriteName), -1)
    return true
end

function GameWorld:removePart(x, y, z, typeId)
    local sq = squareAt(x, y, z)
    local obj = sq and self:objectOf(sq, typeId)
    if not obj then return false end
    sq:transmitRemoveItemFromSquare(obj)
    return true
end

return GameWorld
