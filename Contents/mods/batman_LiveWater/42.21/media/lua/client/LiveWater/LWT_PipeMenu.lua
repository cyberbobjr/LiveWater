-- LiveWater: right-click menu to lay and dismantle the parts laid with an item (capability
-- "layable", e.g. pipes and LiveWater.PipeSection). The player walks to the square and works for a
-- few seconds (timed action LWT_PartAction, LAY_TIME), then the command goes to the authority, which
-- checks everything and answers a refusal with a note (LWT_NoticeClient). Laid on the clicked
-- square: no build cursor (one section per square, the shape follows the neighbours).

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
require "LiveWater/LWT_PartAction"

local PipeMenu = {}

-- Action ticks to lay or dismantle one pipe.
PipeMenu.LAY_TIME = 150

-- Part types laid with an item: list of { id, item }, sorted by id.
function PipeMenu.layables(catalog)
    local out, ids = {}, catalog:ids()
    for i = 1, #ids do
        local item = catalog:first({ type = ids[i] }, "layable")
        if item then out[#out + 1] = { id = ids[i], item = item } end
    end
    return out
end

local function squareOf(worldobjects)
    for i = 1, #worldobjects do
        local sq = worldobjects[i]:getSquare()
        if sq then return sq end
    end
    return nil
end

-- Part type laid on the square, found by the sprite of its objects, or nil.
local function laidTypeOn(sq, catalog)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local name = objects:get(i):getSpriteName()
        local id = name and catalog:typeOfSprite(name)
        if id and catalog:first({ type = id }, "layable") then return id end
    end
    return nil
end

local function send(player, command, sq, part)
    LWT_PartAction.queue(player, sq, command, { part = part }, PipeMenu.LAY_TIME)
end

function PipeMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = squareOf(worldobjects)
    if not player or not sq then return end
    local catalog = LiveWater.Parts
    local laid = laidTypeOn(sq, catalog)
    local inv = player:getInventory()
    local list = PipeMenu.layables(catalog)
    for i = 1, #list do
        local l = list[i]
        local name = getItemNameFromFullType(l.item)
        if laid == l.id then
            if test then return true end
            context:addOption(getText("ContextMenu_LWT_Dismantle", name), player, send, Protocol.DISMANTLE, sq)
        elseif not laid and inv:containsTypeRecurse(l.item) then
            if test then return true end
            context:addOption(getText("ContextMenu_LWT_Lay", name), player, send, Protocol.LAY, sq, l.id)
        end
    end
end

Events.OnFillWorldObjectContextMenu.Add(PipeMenu.fill)

return PipeMenu
