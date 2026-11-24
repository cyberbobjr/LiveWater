-- LiveWater: "Unplumb" on a plumbed water fixture, in a room or on a roof (ADR-024 D04), client.
-- The player walks next to the fixture with a pipe wrench in hand and works as long as for
-- plumbing; the command is then sent and the authority checks again (LWT_CmdUnplumb). The fixture
-- goes back to "set down, to plumb": no more water, the Plumb option comes back.

require "LiveWater/LWT_API"
require "LiveWater/LWT_UnplumbAction"
local Plumbing = require "LiveWater/LWT_Plumbing"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local PartMenu = require "LiveWater/LWT_PartMenu"
local WrenchMenu = require "LiveWater/LWT_WrenchMenu"

local UnplumbMenu = {}

local function plumbed(obj)
    return Plumbing.unplumbRefusal(WaterObjects.plumbInfo(obj)) == nil
end

function UnplumbMenu.start(player, sq, wrench)
    if not luautils.walkAdj(player, sq, true) then return end
    ISWorldObjectContextMenu.equip(player, player:getPrimaryHandItem(), wrench, true)
    ISTimedActionQueue.add(LWT_UnplumbAction:new(player, sq, wrench))
end

function UnplumbMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = PartMenu.squareOf(worldobjects)
    local fixture = player and sq and WrenchMenu.fixtureOn(sq, plumbed)
    if not fixture then return end
    if test then return ISWorldObjectContextMenu.setTest() end
    local wrench = WrenchMenu.wrenchOf(player)
    local text = getText("ContextMenu_LWT_Unplumb", WrenchMenu.nameOf(fixture))
    local option = context:addOption(text, player, UnplumbMenu.start, fixture:getSquare(), wrench)
    WrenchMenu.dress(option, text, wrench, player)
end

Events.OnFillWorldObjectContextMenu.Add(UnplumbMenu.fill)

return UnplumbMenu
