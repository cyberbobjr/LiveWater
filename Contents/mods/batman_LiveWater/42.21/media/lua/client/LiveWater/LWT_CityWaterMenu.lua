-- LiveWater: "Connect to the City Water" on a water fixture a player set down in a room of a map
-- building, while the city water still runs (ADR-001 M01). The client only offers it under the
-- same rule as the server (LWT_CityWater) and sends the command; the authority checks again.

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local CityWater = require "LiveWater/LWT_CityWater"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local PartMenu = require "LiveWater/LWT_PartMenu"

local CityWaterMenu = {}

local function connectableOn(sq)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isFixture(obj)
            and CityWater.refusal(WaterObjects.cityInfo(obj), WaterObjects.cityWaterRuns()) == nil then
            return obj
        end
    end
    return nil
end

function CityWaterMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = PartMenu.squareOf(worldobjects)
    if not player or not sq or not connectableOn(sq) then return end
    if test then return ISWorldObjectContextMenu.setTest() end
    context:addOption(getText("ContextMenu_LWT_CityWater"), player, PartMenu.send, Protocol.CITY_WATER, sq)
end

Events.OnFillWorldObjectContextMenu.Add(CityWaterMenu.fill)

return CityWaterMenu
