-- LiveWater: watered areas, client (ADR-003 D02, D04). Right-click a part that waters (sprinkler, drip
-- line), one option: "Show All Watered Areas" highlights the floor of every square watered by any part
-- around the player (RANGE squares), all in the colour of water; "Hide the Watered Area" clears it. The areas come from the same strategies as the authority (LWT_Plants): sprinklers,
-- the square of their radius (LWT_SprayArea) with the sandbox multiplier (LWT_GameSettings); drip lines,
-- the squares beside them they are not linked to (LWT_DripArea), the links read from the shape sprite.
-- Persistent highlight (setHighlighted(true, false)): no per-frame call, the engine keeps drawing it.
-- A new view replaces the old one. Other mods add a kind with AreaView.addStrategy.

require "LiveWater/LWT_API"
local Mirror = require "LiveWater/LWT_Mirror"
local SprayArea = require "LiveWater/LWT_SprayArea"
local DripArea = require "LiveWater/LWT_DripArea"
local GameSettings = require "LiveWater/LWT_GameSettings"

local AreaView = { shown = {}, strategies = {} }

-- Colour of the watered squares: the blue of water, the same for every kind of part.
AreaView.COLOUR = { 0.25, 0.6, 1.0 }

-- Squares around the player searched by "Show All Watered Areas".
AreaView.RANGE = 25

-- The LiveWater part on a square, as { type, data, x, y, z, sprite }, or nil.
local function partOn(sq)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        local name = obj:getSpriteName()
        local id = name and LiveWater.Parts:typeOfSprite(name)
        if id then
            local state = Mirror.read(obj)
            return { type = id, data = state and state.type == id and state.data or {},
                x = sq:getX(), y = sq:getY(), z = sq:getZ(), sprite = name }
        end
    end
    return nil
end

-- Links of a part read from its shape sprite (the client has no network graph): the `network` the
-- drip strategy asks, mask(x, y, z) -> side mask, 0 when the sprite is not a shape.
local Shapes = {}
function Shapes:mask(x, y, z)
    local sq = getCell():getGridSquare(x, y, z)
    local part = sq and partOn(sq)
    if not part then return 0 end
    for mask = 0, 15 do
        if LiveWater.Parts:hasShape(part.type, mask) and LiveWater.Parts:sprite(part.type, mask) == part.sprite then
            return mask
        end
    end
    return 0
end

-- A kind of watering part: `reach` is an area strategy (function(part) -> squares, ...) giving no
-- squares for a part it does not handle.
function AreaView.addStrategy(reach)
    AreaView.strategies[#AreaView.strategies + 1] = reach
end

AreaView.addStrategy(SprayArea.reach(LiveWater.Parts, GameSettings.scale))
AreaView.addStrategy(DripArea.reach(LiveWater.Parts, Shapes, GameSettings.scale))

-- Squares a part waters, or nil when it waters nothing.
local function areaOf(part)
    for i = 1, #AreaView.strategies do
        local squares = AreaView.strategies[i](part)
        if #squares > 0 then return squares end
    end
    return nil
end

function AreaView.clear()
    for i = 1, #AreaView.shown do AreaView.shown[i]:setHighlighted(false, false) end
    AreaView.shown = {}
end

local function light(cell, squares, z)
    local colour = AreaView.COLOUR
    for i = 1, #squares do
        local sq = cell:getGridSquare(squares[i].x, squares[i].y, z)
        local floor = sq and sq:getFloor()
        if floor then
            floor:setHighlightColor(colour[1], colour[2], colour[3], 1)
            floor:setHighlighted(true, false)
            AreaView.shown[#AreaView.shown + 1] = floor
        end
    end
end

-- Parts that water on the loaded squares around (x, y, z).
local function wateringAround(x, y, z)
    local cell, out = getCell(), {}
    for dx = -AreaView.RANGE, AreaView.RANGE do
        for dy = -AreaView.RANGE, AreaView.RANGE do
            local sq = cell:getGridSquare(x + dx, y + dy, z)
            local part = sq and partOn(sq)
            if part and areaOf(part) then out[#out + 1] = part end
        end
    end
    return out
end

function AreaView.showAll(parts)
    AreaView.clear()
    local cell = getCell()
    for i = 1, #parts do
        light(cell, areaOf(parts[i]), parts[i].z)
    end
end

local function squareOf(worldobjects)
    for i = 1, #worldobjects do
        local sq = worldobjects[i]:getSquare()
        if sq then return sq end
    end
    return nil
end

function AreaView.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = squareOf(worldobjects)
    if not player or not sq then return end
    local part = partOn(sq)
    -- one option at a time (ADR-008 D04): Hide while areas are lit, else Show
    if part and #AreaView.shown == 0 and areaOf(part) then
        if test then return true end
        -- bounded scan (RANGE), only on a part that waters and when the menu really opens
        local around = wateringAround(math.floor(player:getX()), math.floor(player:getY()), math.floor(player:getZ()))
        context:addOption(getText("ContextMenu_LWT_ShowAllAreas"), around, AreaView.showAll)
    end
    if test then return end
    if #AreaView.shown > 0 then
        context:addOption(getText("ContextMenu_LWT_HideArea"), nil, AreaView.clear)
    end
end

Events.OnFillWorldObjectContextMenu.Add(AreaView.fill)

return AreaView
