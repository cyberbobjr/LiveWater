-- LiveWater: right-click menu of the parts that have actions (fit or remove a filter, switch a
-- pump...). It reads the state mirrored on the object (LWT_Mirror, synced by the server), asks
-- the part's capabilities for their actions (`actions` hook) and only sends the command; the
-- server checks everything and answers a refusal with a note (LWT_NoticeClient). An action
-- that needs an item is offered only when the player carries one.

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local Mirror = require "LiveWater/LWT_Mirror"

local PartMenu = {}

local function squareOf(worldobjects)
    for i = 1, #worldobjects do
        local sq = worldobjects[i]:getSquare()
        if sq then return sq end
    end
    return nil
end

-- Parts on the square, as { type, data } from their mirrored state (data {} when none yet).
function PartMenu.partsOn(sq, catalog)
    local out, objects = {}, sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        local name = obj:getSpriteName()
        local id = name and catalog:typeOfSprite(name)
        if id then
            local state = Mirror.read(obj)
            local data = state and state.type == id and state.data or {}
            out[#out + 1] = { type = id, data = data, object = obj }
        end
    end
    return out
end

local function send(player, command, sq)
    sendClientCommand(player, Protocol.MODULE, command, { x = sq:getX(), y = sq:getY(), z = sq:getZ() })
end

function PartMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = squareOf(worldobjects)
    if not player or not sq then return end
    local catalog, inv = LiveWater.Parts, player:getInventory()
    local parts = PartMenu.partsOn(sq, catalog)
    for i = 1, #parts do
        local actions = catalog:actions(parts[i])
        for j = 1, #actions do
            local a = actions[j]
            if a.item == nil or inv:containsTypeRecurse(a.item) then
                if test then return true end
                context:addOption(getText(a.key), player, send, a.command, sq)
            end
        end
    end
end

Events.OnFillWorldObjectContextMenu.Add(PartMenu.fill)

return PartMenu
