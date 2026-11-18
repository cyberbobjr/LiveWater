-- LiveWater: view of a water network, client (ADR-001 D11, D14, D17). Right-click a part: "Show the
-- Water Network" asks the authority for the squares of its network (command showNetwork, reply
-- network); each part there is highlighted, persistently (setHighlighted(true, false): no per-frame
-- call, the engine keeps drawing it), in the colour of its state: an outlet that gets water, one
-- without pressure, one refused unfiltered water, the other parts (pipes, pumps). "Hide the Water
-- Network" clears it; its tooltip tells how many outlets are in each state. A new view replaces the
-- old one. Colours are data (COLOURS by status token, `status` hook of the capabilities).

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local Mirror = require "LiveWater/LWT_Mirror"
local PartMenu = require "LiveWater/LWT_PartMenu"

local View = { shown = {}, counts = {} }

-- status token -> { r, g, b }, and the legend group it counts in.
View.COLOURS = {
    served = { 0.3, 0.9, 0.3, group = "served" },
    idle = { 0.3, 0.9, 0.3, group = "served" },
    no_pressure = { 1.0, 0.25, 0.2, group = "no_pressure" },
    unfiltered = { 1.0, 0.7, 0.1, group = "unfiltered" },
    no_water = { 0.6, 0.6, 0.7, group = "other" },
    closed = { 0.6, 0.6, 0.7, group = "other" },
    wrong_fluid = { 0.6, 0.6, 0.7, group = "other" },
}
View.DEFAULT = { 0.3, 0.6, 1.0 }
View.GROUPS = { "served", "no_pressure", "unfiltered", "other" }

-- The LiveWater part object of a square and its part ({ type, data }), or nil.
local function partOn(sq)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        local name = obj:getSpriteName()
        local id = name and LiveWater.Parts:typeOfSprite(name)
        if id then
            local state = Mirror.read(obj)
            return obj, { type = id, data = state and state.type == id and state.data or {} }
        end
    end
    return nil
end

function View.clear()
    for i = 1, #View.shown do View.shown[i]:setHighlighted(false, false) end
    View.shown, View.counts = {}, {}
end

-- Highlight the parts of the squares the authority sent.
function View.show(list)
    View.clear()
    local cell = getCell()
    for i = 1, #list do
        local e = list[i]
        local sq = cell:getGridSquare(e.x, e.y, e.z)
        local obj, part = nil, nil
        if sq then obj, part = partOn(sq) end
        if obj then
            local status = LiveWater.Parts:first(part, "status")
            local colour = status and View.COLOURS[status] or View.DEFAULT
            if colour.group then View.counts[colour.group] = (View.counts[colour.group] or 0) + 1 end
            obj:setHighlightColor(colour[1], colour[2], colour[3], 1)
            obj:setHighlighted(true, false)
            View.shown[#View.shown + 1] = obj
        end
    end
end

function View.legend()
    local out = { getText("IGUI_LWT_View_Title") }
    for i = 1, #View.GROUPS do
        local g = View.GROUPS[i]
        local key = "IGUI_LWT_View_" .. g
        out[#out + 1] = getText(key, string.format("%d", View.counts[g] or 0))
    end
    return table.concat(out, " <LINE> ")
end

local function ask(player, sq)
    sendClientCommand(player, Protocol.MODULE, Protocol.SHOW_NETWORK, { x = sq:getX(), y = sq:getY(), z = sq:getZ() })
end

function View.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = PartMenu.squareOf(worldobjects)
    if not player or not sq then return end
    if partOn(sq) then
        if test then return true end
        context:addOption(getText("ContextMenu_LWT_ShowNetwork"), player, ask, sq)
    end
    if #View.shown > 0 and not test then
        local option = context:addOption(getText("ContextMenu_LWT_HideNetwork"), nil, View.clear)
        local tooltip = ISToolTip:new()
        tooltip:initialise()
        tooltip:setName(getText("ContextMenu_LWT_HideNetwork"))
        tooltip.description = View.legend()
        option.toolTip = tooltip
    end
end

function View.onServerCommand(module, command, args)
    if module ~= Protocol.MODULE or command ~= Protocol.NETWORK or type(args) ~= "table" then return end
    if type(args.parts) == "table" then View.show(args.parts) end
end

Events.OnFillWorldObjectContextMenu.Add(View.fill)
Events.OnServerCommand.Add(View.onServerCommand)

return View
