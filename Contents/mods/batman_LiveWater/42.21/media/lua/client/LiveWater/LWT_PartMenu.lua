-- LiveWater: right-click menu of the parts that have actions (fit or remove a filter, switch or
-- repair a pump...) or information lines (state, power, source, efficiency, filter: P08). It
-- reads the state mirrored on the object (LWT_Mirror, synced by the server), asks the part's
-- capabilities for their actions (`actions` hook) and lines (`lines` hook), and only sends the
-- command; the server checks everything and answers a refusal with a note (LWT_NoticeClient).
-- An action that needs an item is offered only when the player carries one. The information is
-- the tooltip of an "Information" option: nothing is drawn per frame by LiveWater.

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local Mirror = require "LiveWater/LWT_Mirror"

local PartMenu = {}

-- Square of the clicked objects, or nil (shared with the other LiveWater menus).
function PartMenu.squareOf(worldobjects)
    for i = 1, #worldobjects do
        local sq = worldobjects[i]:getSquare()
        if sq then return sq end
    end
    return nil
end
local squareOf = PartMenu.squareOf

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

-- Argument of a line as text: a whole number without a decimal part (a Lua number reaches
-- Java's getText as a Double, "50.0").
local function asText(v)
    if type(v) == "number" and v % 1 == 0 then return string.format("%d", v) end
    return tostring(v)
end

-- Text of the information lines of a part (`lines` hooks, P08), one per line of the tooltip.
function PartMenu.describe(catalog, part)
    local lines, out = catalog:lines(part), {}
    for i = 1, #lines do
        local l, args = lines[i], {}
        for j = 2, #l do args[j - 1] = asText(l[j]) end
        out[i] = getText(l[1], unpack(args))
    end
    return table.concat(out, " <LINE> ")
end

-- "Information" option: its tooltip shows the lines; choosing it does nothing more.
local function addInformation(context, catalog, part)
    if #catalog:lines(part) == 0 then return end
    local option = context:addOption(getText("ContextMenu_LWT_Info"), nil, nil)
    local tooltip = ISToolTip:new()
    tooltip:initialise()
    tooltip:setName(getText("ContextMenu_LWT_Info"))
    tooltip.description = PartMenu.describe(catalog, part)
    option.toolTip = tooltip
end

-- Send a command about a square to the authority (shared with the other LiveWater menus).
function PartMenu.send(player, command, sq)
    sendClientCommand(player, Protocol.MODULE, command, { x = sq:getX(), y = sq:getY(), z = sq:getZ() })
end
local send = PartMenu.send

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
        if not test then addInformation(context, catalog, parts[i]) end
    end
end

Events.OnFillWorldObjectContextMenu.Add(PartMenu.fill)

return PartMenu
