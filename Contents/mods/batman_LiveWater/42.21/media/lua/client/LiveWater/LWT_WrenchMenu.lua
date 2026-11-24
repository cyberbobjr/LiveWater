-- LiveWater: what the pipe wrench options of a water fixture share (ADR-024), client. Same wrench
-- rule, name, icon and tooltip as the game's own "Plumb" option (ISWorldObjectContextMenuLogic
-- .doWaterPipeMenu, Java 42.22; ISWorldObjectContextMenu.onPlumbItem), through the shared rule of
-- LWT_Wrench: the authority's command asks the same module.
--   fixtureOn(sq, wanted)   first water fixture of the square that wanted(obj) accepts, or nil
--   nameOf(obj)             display name of the fixture ("" when it has none)
--   wrenchOf(player)        a pipe wrench that is not broken in the inventory (bags included), or nil
--   needText(player)        the tooltip line of an option the player may not use: the game's own
--                           "%1 required.", or the broken pipe wrench he carries (the game hides it)
--   dress(option, text, wrench, player)  the wrench icon; without a wrench the option is greyed and
--                                says which tool is needed, or that the pipe wrench is broken

local WaterObjects = require "LiveWater/LWT_WaterObjects"
local Wrench = require "LiveWater/LWT_Wrench"

local WrenchMenu = {}

-- Translation keys of the game itself (42.22 Translate/EN: ContextMenu.json "Plumb %1",
-- Tooltip.json "%1 required."): the option reads as the game's own in every language.
WrenchMenu.PLUMB_KEY = "ContextMenu_PlumbItem"
WrenchMenu.NEED_KEY = "Tooltip_NeedWrench"

function WrenchMenu.fixtureOn(sq, wanted)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isFixture(obj) and wanted(obj) then return obj end
    end
    return nil
end

function WrenchMenu.nameOf(obj)
    local sprite = obj:getSprite()
    local props = sprite and sprite:getProperties()
    if not props or not props:has("CustomName") then return "" end
    local name = props:get("CustomName")
    if props:has("GroupName") then name = props:get("GroupName") .. " " .. name end
    return Translator.getMoveableDisplayName(name)
end

function WrenchMenu.wrenchOf(player)
    return Wrench.of(player)
end

function WrenchMenu.needText(player)
    if Wrench.problem(player) == "wrench_broken" then return getText("IGUI_LWT_WrenchBroken") end
    return getText(WrenchMenu.NEED_KEY, getItemName("Base.PipeWrench"))
end

function WrenchMenu.dress(option, text, wrench, player)
    option.iconTexture = getTexture("Item_PipeWrench")
    if wrench then return end
    option.notAvailable = true
    local tip = ISWorldObjectContextMenu.addToolTip()
    tip:setName(text)
    tip.description = WrenchMenu.needText(player)
    option.toolTip = tip
end

return WrenchMenu
