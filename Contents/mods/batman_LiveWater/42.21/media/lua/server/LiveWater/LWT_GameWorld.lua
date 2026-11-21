if isClient() then return end
-- LiveWater: game adapter of the world port (squares and part objects), authority only. Thin:
-- every decision is in the services that use it (LWT_Sprites, LWT_Clock, commands).
--   isLoaded(x, y, z)                 square loaded (getCell():getGridSquare non-nil)
--   spriteOf(x, y, z, typeId)         sprite of the object of that part type on the square
--   setSprite(x, y, z, typeId, name)  setSpriteFromName + transmitUpdatedSpriteToClients
--   removePart(x, y, z, typeId)       remove the object of that part type, sent to the clients
--   object(x, y, z, typeId)           the object of that part type, or nil
--   site(x, y, z)                     the place, for Parts:attach (LWT_GameSite, with the barrels
--                                     given to new: { registry, listed })
--   hasPower(x, y, z)                 vanilla rule for an appliance outdoors or indoors: a
--                                     generator in range or the public grid (PowerPolicy
--                                     ExteriorOK of ObjectAmbientEmitters, Java 42.22)
--   powerAt(x, y, z)                  the two parts of that rule on a loaded square: generator
--                                     (IsoGridSquare.haveElectricity) and grid (hasGridPower:
--                                     the square has the public grid and it still runs); nil
--                                     when not loaded
--   gridRuns()                        the public grid still runs in the world, wherever a square
--                                     is loaded or not (SandboxOptions.doesPowerGridExist: world
--                                     age in days <= ElecShutModifier, SandboxOptions.java:1223)
--   writeState(x, y, z, typeId, s)    mirror the state on the object and send it (LWT_Mirror)
--   stateOf(x, y, z, typeId)          state mirrored on the object, or nil
--   stateOfObject(obj)                state mirrored on a game object, or nil
--   edge(x, y, z, north)              "wall", "fence" or nil: what the N (north) or W edge of the
--                                     square carries (ADR-002 D01-D02, rule of the engine's
--                                     IsoGridSquare.hasNonHoppableWall), nil when not loaded
--   isEdgeObject(obj)                 the object stands on an edge (wall, fence): links may change
--   without(obj, fn)                  run fn() as if obj were gone (an object about to be removed)
-- The part type of an object is found by its sprite through the part catalog.

local GameSite = require "LiveWater/LWT_GameSite"
local Mirror = require "LiveWater/LWT_Mirror"

local GameWorld = {}
GameWorld.__index = GameWorld

function GameWorld.new(catalog, sources, barrels)
    return setmetatable({ catalog = catalog, sources = sources, barrels = barrels }, GameWorld)
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

-- Sprite flags of an edge: wall flags, fence flags (Java 42.22 IsoGridSquare.java:3840-3891).
local EDGE_FLAGS = {
    [true] = { wall = { "cutN", "WallN", "WallNTrans", "WallNW" }, fence = { "HoppableN", "TallHoppableN" } },
    [false] = { wall = { "cutW", "WallW", "WallWTrans", "WallNW" }, fence = { "HoppableW", "TallHoppableW" } },
}

local function hasAny(props, names)
    for i = 1, #names do
        if props:has(IsoFlagType[names[i]]) then return true end
    end
    return false
end

-- "wall", "fence" or nil for one object on the N (north) or W edge. The south-east corner post of a
-- building (WallSE) carries cutW and is no wall: the engine skips it (IsoGridSquare.java:3882).
local function edgeKindOf(obj, north)
    local props = obj:getProperties()
    if not props or props:has(IsoFlagType.WallSE) then return nil end
    local flags = EDGE_FLAGS[north]
    if hasAny(props, flags.fence) then return "fence" end
    if hasAny(props, flags.wall) then return "wall" end
    if instanceof(obj, "IsoWindow") and obj:isNorth() == north then return "wall" end
    return nil
end

function GameWorld:edge(x, y, z, north)
    local sq = squareAt(x, y, z)
    if not sq then return nil end
    local objects, kind = sq:getObjects(), nil
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if obj ~= self.ignored then
            local k = edgeKindOf(obj, north)
            if k == "wall" then return "wall" end
            kind = kind or k
        end
    end
    return kind
end

function GameWorld:isEdgeObject(obj)
    return edgeKindOf(obj, true) ~= nil or edgeKindOf(obj, false) ~= nil
end

function GameWorld:without(obj, fn)
    self.ignored = obj
    fn()
    self.ignored = nil
end

function GameWorld:isLoaded(x, y, z)
    return squareAt(x, y, z) ~= nil
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
    return GameSite.new(self.sources, x, y, z, self.barrels)
end

function GameWorld:hasPower(x, y, z)
    local sq = squareAt(x, y, z)
    return sq ~= nil and (sq:haveElectricity() or sq:hasGridPower())
end

function GameWorld:powerAt(x, y, z)
    local sq = squareAt(x, y, z)
    if not sq then return nil end
    return sq:haveElectricity() == true, sq:hasGridPower() == true
end

function GameWorld:gridRuns()
    local options = getSandboxOptions()
    return options ~= nil and options:doesPowerGridExist() == true
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

function GameWorld:removePart(x, y, z, typeId)
    local sq = squareAt(x, y, z)
    local obj = sq and self:objectOf(sq, typeId)
    if not obj then return false end
    sq:transmitRemoveItemFromSquare(obj)
    return true
end

return GameWorld
