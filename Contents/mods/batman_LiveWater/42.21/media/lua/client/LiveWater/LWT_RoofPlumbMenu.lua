-- LiveWater: the game's "Plumb" option for a water fixture on a roof (ADR-024 D01, D02), client.
-- The game offers it only in a room; on a roof (outside any room, right above a room) with a tank
-- above the fixture, LiveWater offers the same option: same text, icon, wrench and vanilla action
-- (ISWorldObjectContextMenu.onPlumbItem -> ISPlumbItem, completed on the authority and watched by
-- LWT_PlumbWatch). The rule (LWT_Plumbing.plumbOffer) never holds where the game's own does.

require "LiveWater/LWT_API"
local Plumbing = require "LiveWater/LWT_Plumbing"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local PartMenu = require "LiveWater/LWT_PartMenu"
local WrenchMenu = require "LiveWater/LWT_WrenchMenu"

local RoofPlumbMenu = {}

local function offered(obj)
    return Plumbing.plumbOffer(WaterObjects.plumbInfo(obj))
end

function RoofPlumbMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = PartMenu.squareOf(worldobjects)
    local fixture = player and sq and WrenchMenu.fixtureOn(sq, offered)
    if not fixture then return end
    if test then return ISWorldObjectContextMenu.setTest() end
    local text = getText(WrenchMenu.PLUMB_KEY, WrenchMenu.nameOf(fixture))
    local option = context:addGetUpOption(text, worldobjects, ISWorldObjectContextMenu.onPlumbItem, playerNum, fixture)
    WrenchMenu.dress(option, text, WrenchMenu.wrenchOf(player), player)
end

Events.OnFillWorldObjectContextMenu.Add(RoofPlumbMenu.fill)

return RoofPlumbMenu
