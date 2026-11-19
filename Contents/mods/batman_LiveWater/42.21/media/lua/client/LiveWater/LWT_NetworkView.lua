-- LiveWater: view of a water network, client (ADR-001 D11, D14, D17). Right-click a part: "Show the
-- Water Network" asks the authority for the squares of its network (command showNetwork, reply
-- network); each part there is highlighted, persistently (setHighlighted(true, false): no per-frame
-- call, the engine keeps drawing it), in the colour of its state: an outlet that gets water, one
-- without pressure, one refused unfiltered water, the other parts (pipes, pumps). "Hide the Water
-- Network" clears it; its tooltip tells how many outlets are in each state. A new view replaces the
-- old one. Colours are data (COLOURS by status token, `status` hook of the capabilities).
-- The reply also lists the fixtures of the area of each house inlet of the network (ADR-008 D06):
-- each one is highlighted by how it gets water (FIXTURES by status: fed green, dry red, not
-- plumbed amber, fed by something else grey), and the tooltip counts them too.

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local Mirror = require "LiveWater/LWT_Mirror"
local PartMenu = require "LiveWater/LWT_PartMenu"
local WaterObjects = require "LiveWater/LWT_WaterObjects"

local View = { shown = {}, counts = {}, fixtures = 0 }

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
-- fixture status (LWT_Relays.fixtureStates) -> { r, g, b }, and its legend group.
View.FIXTURES = {
    fed = { 0.3, 0.9, 0.3, group = "fixtures_fed" },
    dry = { 1.0, 0.25, 0.2, group = "fixtures_dry" },
    notPlumbed = { 1.0, 0.7, 0.1, group = "fixtures_notPlumbed" },
    other = { 0.6, 0.6, 0.7, group = "fixtures_other" },
}
View.FIXTURE_GROUPS = { "fixtures_fed", "fixtures_dry", "fixtures_notPlumbed", "fixtures_other" }

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

-- The water fixture object of a square, or nil.
local function fixtureOn(sq)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isFixture(obj) then return obj end
    end
    return nil
end

function View.clear()
    for i = 1, #View.shown do View.shown[i]:setHighlighted(false, false) end
    View.shown, View.counts, View.fixtures = {}, {}, 0
end

-- Highlight an object in a colour, counted in its legend group.
local function highlight(obj, colour)
    if colour.group then View.counts[colour.group] = (View.counts[colour.group] or 0) + 1 end
    obj:setHighlightColor(colour[1], colour[2], colour[3], 1)
    obj:setHighlighted(true, false)
    View.shown[#View.shown + 1] = obj
end

-- Highlight the parts of the squares the authority sent, then the fixtures (optional list).
function View.show(list, fixtures)
    View.clear()
    local cell = getCell()
    for i = 1, #list do
        local e = list[i]
        local sq = cell:getGridSquare(e.x, e.y, e.z)
        local obj, part = nil, nil
        if sq then obj, part = partOn(sq) end
        if obj then
            local status = LiveWater.Parts:first(part, "status")
            highlight(obj, status and View.COLOURS[status] or View.DEFAULT)
        end
    end
    for i = 1, #(fixtures or {}) do
        local f = fixtures[i]
        local colour = type(f) == "table" and View.FIXTURES[f.status]
        local sq = colour and cell:getGridSquare(f.x, f.y, f.z)
        local obj = sq and fixtureOn(sq)
        if obj then
            highlight(obj, colour)
            View.fixtures = View.fixtures + 1
        end
    end
end

local function addGroups(out, groups)
    for i = 1, #groups do
        local g = groups[i]
        local key = "IGUI_LWT_View_" .. g
        out[#out + 1] = getText(key, string.format("%d", View.counts[g] or 0))
    end
end

-- Lines of the tooltip: the parts' groups, then the fixtures' groups when some were shown.
function View.legend()
    local out = { getText("IGUI_LWT_View_Title") }
    addGroups(out, View.GROUPS)
    if View.fixtures > 0 then addGroups(out, View.FIXTURE_GROUPS) end
    return table.concat(out, " <LINE> ")
end

local function ask(player, sq)
    sendClientCommand(player, Protocol.MODULE, Protocol.SHOW_NETWORK, { x = sq:getX(), y = sq:getY(), z = sq:getZ() })
end

function View.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = PartMenu.squareOf(worldobjects)
    if not player or not sq then return end
    -- one option at a time (ADR-008 D04): Hide while a view is shown, else Show
    local shown = #View.shown > 0
    if partOn(sq) and not shown then
        if test then return true end
        context:addOption(getText("ContextMenu_LWT_ShowNetwork"), player, ask, sq)
    end
    if shown and not test then
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
    if type(args.parts) == "table" then
        View.show(args.parts, type(args.fixtures) == "table" and args.fixtures or nil)
    end
end

Events.OnFillWorldObjectContextMenu.Add(View.fill)
Events.OnServerCommand.Add(View.onServerCommand)

return View
