-- LiveWater: minimal right-click menu to lay and dismantle the parts laid with an item
-- (capability "layable", e.g. pipes and LiveWater.PipeSection). It only sends the command;
-- the server checks everything and answers a refusal with a note (LWT_NoticeClient). The full
-- interface (timed actions, network view) comes with plan step E13.

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"

local PipeMenu = {}

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
    sendClientCommand(player, Protocol.MODULE, command, { x = sq:getX(), y = sq:getY(), z = sq:getZ(), part = part })
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
