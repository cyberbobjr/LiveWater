-- LiveWater: right-click menu of a barrel or rain collector (ADR-001 D28, L01, L06): connect it to
-- the house water inlet of its building, disconnect it, keep it in reserve or use it with the
-- others. Reads the connection mirrored on the barrel (ModData LiveWaterBarrel, LWT_WaterObjects)
-- and only sends the command; the authority checks everything (pipe wrench, reach, an inlet whose
-- building holds the barrel or its roof) and answers a refusal with a note.

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local PartMenu = require "LiveWater/LWT_PartMenu"

local BarrelMenu = {}

local function barrelOn(sq)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isBarrel(obj) then return obj end
    end
    return nil
end

-- Options for the barrel: { { key, command } } from its mirrored connection.
function BarrelMenu.options(mark)
    if not mark then return { { "ContextMenu_LWT_ConnectBarrel", Protocol.CONNECT_BARREL } } end
    local reserve = mark.reserve and "ContextMenu_LWT_UseBarrel" or "ContextMenu_LWT_ReserveBarrel"
    return { { reserve, Protocol.RESERVE_BARREL }, { "ContextMenu_LWT_DisconnectBarrel", Protocol.DISCONNECT_BARREL } }
end

function BarrelMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = PartMenu.squareOf(worldobjects)
    local barrel = sq and barrelOn(sq)
    if not player or not barrel then return end
    if test then return ISWorldObjectContextMenu.setTest() end
    local options = BarrelMenu.options(WaterObjects.mark(barrel, WaterObjects.BARREL_KEY))
    for i = 1, #options do
        context:addOption(getText(options[i][1]), player, PartMenu.send, options[i][2], sq)
    end
end

Events.OnFillWorldObjectContextMenu.Add(BarrelMenu.fill)

return BarrelMenu
