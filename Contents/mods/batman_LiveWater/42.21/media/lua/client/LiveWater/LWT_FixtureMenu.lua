-- LiveWater: a water fixture without water says why, in one line of its right-click menu (ADR-001
-- D28, L09). Reads what the client sees: the fixture is plumbed or not, the tank the engine would
-- draw from (IsoObject.FindExternalWaterSource: one of LiveWater's relays, something else, or
-- nothing) and the reason the authority noted on our relay (ModData LiveWaterRelay.why,
-- LWT_Diagnostics). The line is a disabled option whose text is the reason (LWT_Diagnosis).

require "LiveWater/LWT_API"
local Diagnosis = require "LiveWater/LWT_Diagnosis"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local PartMenu = require "LiveWater/LWT_PartMenu"

local FixtureMenu = {}

-- A fixture that would draw from an outside source and has no water now, or nil.
local function dryFixtureOn(sq)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isFixture(obj) and obj:getFluidAmount() <= 0
            and (obj:getUsesExternalWaterSource() or obj:getModData().canBeWaterPiped == true
                or not WaterObjects.cityWaterRuns()) then
            return obj
        end
    end
    return nil
end

-- Information on the fixture for LWT_Diagnosis.fixture.
function FixtureMenu.infoOf(fixture, sq)
    local src = IsoObject.FindExternalWaterSource(sq)
    local mark = WaterObjects.mark(src, WaterObjects.RELAY_KEY)
    local source = src and (mark and "ours" or "other") or nil
    return { plumbed = fixture:getUsesExternalWaterSource(), source = source, why = mark and mark.why or nil }
end

function FixtureMenu.fill(playerNum, context, worldobjects, test)
    local sq = PartMenu.squareOf(worldobjects)
    local fixture = sq and dryFixtureOn(sq)
    if not fixture or test then return end
    local key = Diagnosis.fixture(FixtureMenu.infoOf(fixture, sq))
    local option = context:addOption(getText("ContextMenu_LWT_NoWater", getText(key)), nil, nil)
    option.notAvailable = true
end

Events.OnFillWorldObjectContextMenu.Add(FixtureMenu.fill)

return FixtureMenu
