-- LiveWater: right-click menu of the parts that have actions (fit or remove a filter, switch or
-- repair a pump...) or information lines (state, power, source, efficiency, filter: P08). It
-- reads the state mirrored on the object (LWT_Mirror, synced by the server), asks the part's
-- capabilities for their actions (`actions` hook) and lines (`lines` hook); a chosen action walks the
-- player to the square and runs a short timed action that sends the command (LWT_PartAction, E13);
-- the server checks everything and answers a refusal with a note (LWT_NoticeClient).
-- A part whose capability names a window face (`panel` hook, ADR-008: the water meter, the pump's
-- LCD) opens that window from "Information" (LWT_Panels); the others keep the tooltip.
-- An action that needs an item is offered only when the player carries one; an action with
-- `choices` (a timer's hours) opens a submenu whose choice sends its args with the command. The
-- information is the tooltip of an "Information" option: nothing is drawn per frame by LiveWater.

require "LiveWater/LWT_API"
local Mirror = require "LiveWater/LWT_Mirror"
local PartText = require "LiveWater/LWT_PartText"
local Panels = require "LiveWater/LWT_Panels"
require "LiveWater/LWT_PartAction"

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

local asText = PartText.asText

-- Text of the information lines of a part (`lines` hooks, P08), one per line of the tooltip.
function PartMenu.describe(catalog, part)
    return table.concat(PartText.texts(catalog, part), " <LINE> ")
end

-- "Information" option: opens the part's window when its capability names a registered face,
-- else its tooltip shows the lines and choosing it does nothing more.
local function addInformation(context, catalog, part, player)
    if #catalog:lines(part, PartText.CTX) == 0 then return end
    local face = catalog:first(part, "panel")
    if Panels.get(face) then
        context:addOption(getText("ContextMenu_LWT_Info"), player, Panels.open, face, part)
        return
    end
    local option = context:addOption(getText("ContextMenu_LWT_Info"), nil, nil)
    local tooltip = ISToolTip:new()
    tooltip:initialise()
    tooltip:setName(getText("ContextMenu_LWT_Info"))
    tooltip.description = PartMenu.describe(catalog, part)
    option.toolTip = tooltip
end

-- Act on a square (shared with the other LiveWater menus): walk there, a short timed action, then the
-- command to the authority; `extra` (optional) adds arguments.
function PartMenu.send(player, command, sq, extra)
    LWT_PartAction.queue(player, sq, command, extra)
end
local send = PartMenu.send

-- One option, or a submenu of its choices.
local function addAction(context, player, sq, a)
    if not a.choices then
        context:addOption(getText(a.key), player, send, a.command, sq)
        return
    end
    local option = context:addOption(getText(a.key), nil, nil)
    local sub = ISContextMenu:getNew(context)
    context:addSubMenu(option, sub)
    for i = 1, #a.choices do
        local c = a.choices[i]
        sub:addOption(getText(c.key, asText(c.arg)), player, send, a.command, sq, c.args)
    end
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
                addAction(context, player, sq, a)
            end
        end
        if not test then addInformation(context, catalog, parts[i], player) end
    end
end

Events.OnFillWorldObjectContextMenu.Add(PartMenu.fill)

return PartMenu
