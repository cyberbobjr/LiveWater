-- LiveWater: one line about the water of a fixture in its right-click menu, client (ADR-001 D28, L09;
-- ADR-008 D05). Reads what the client sees: the fixture is plumbed or not, the tank the engine would
-- draw from (IsoObject.FindExternalWaterSource: one of LiveWater's relays, something else, or
-- nothing) and the reason the authority noted on our relay (ModData LiveWaterRelay.why,
-- LWT_Diagnostics). The line is a disabled option, the first that LINES gives for the fixture:
--   water  a plumbed fixture fed by one of LiveWater's relays that has water: "Water: 18 L / 25 L"
--          (its water, the relay's capacity)
--   dry    a fixture that would draw from an outside source and has no water: why (LWT_Diagnosis).
--          A fixture waiting to be plumbed also says when the local player carries no pipe wrench, or
--          only broken ones: the game's own option hides it (LWT_Wrench).

require "LiveWater/LWT_API"
local Diagnosis = require "LiveWater/LWT_Diagnosis"
local Settings = require "LiveWater/LWT_Settings"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local Wrench = require "LiveWater/LWT_Wrench"
local PartMenu = require "LiveWater/LWT_PartMenu"

local FixtureMenu = {}

-- Translation keys of what stops the local player from plumbing a fixture waiting for it.
FixtureMenu.PROBLEM_KEYS = { no_wrench = "IGUI_LWT_NoWrench", wrench_broken = "IGUI_LWT_WrenchBroken" }

-- Information on the fixture for LWT_Diagnosis.fixture.
function FixtureMenu.infoOf(fixture, sq)
    local src = IsoObject.FindExternalWaterSource(sq)
    local mark = WaterObjects.mark(src, WaterObjects.RELAY_KEY)
    local source = src and (mark and "ours" or "other") or nil
    return { plumbed = fixture:getUsesExternalWaterSource(), source = source, why = mark and mark.why or nil }
end

-- Litres in the fixture and the capacity of the relay of LiveWater that feeds it, or nil.
function FixtureMenu.waterOf(fixture, sq)
    if not fixture:getUsesExternalWaterSource() then return nil end
    local amount = fixture:getFluidAmount()
    if amount <= 0 then return nil end
    local src = IsoObject.FindExternalWaterSource(sq)
    if not WaterObjects.mark(src, WaterObjects.RELAY_KEY) then return nil end
    local fc = src:getFluidContainer()
    return amount, fc and fc:getCapacity() or WaterObjects.RELAY_LITRES
end

local function waterLine(fixture, sq)
    local amount, capacity = FixtureMenu.waterOf(fixture, sq)
    if not amount then return nil end
    return getText("ContextMenu_LWT_Water", Settings.litres(amount), Settings.litres(capacity)), false
end

-- A fixture that would draw from an outside source and has no water now.
local function isDry(obj)
    return obj:getFluidAmount() <= 0 and (obj:getUsesExternalWaterSource() or obj:getModData().canBeWaterPiped == true
        or not WaterObjects.cityWaterRuns())
end

local function dryLine(fixture, sq, player)
    if not isDry(fixture) then return nil end
    local info = FixtureMenu.infoOf(fixture, sq)
    local text = getText(Diagnosis.fixture(info))
    -- a fixture our relay stands above that nobody plumbed yet: the player's own wrench is the next
    -- step, so name what stops him
    if not info.plumbed and info.source then
        local hint = FixtureMenu.PROBLEM_KEYS[Wrench.problem(player)]
        if hint then text = text .. ". " .. getText(hint) end
    end
    return getText("ContextMenu_LWT_NoWater", text), true
end

FixtureMenu.LINES = { waterLine, dryLine }

-- Each producer returns its text and whether it reports a fault (drawn red) rather than information
-- (greyed). The line of the first fixture of the square that has one: text, fault; or nil. `player`
-- is the local player, or nil (no wrench hint then).
function FixtureMenu.lineOn(sq, player)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        if WaterObjects.isFixture(obj) then
            for j = 1, #FixtureMenu.LINES do
                local text, fault = FixtureMenu.LINES[j](obj, sq, player)
                if text then return text, fault end
            end
        end
    end
    return nil
end

function FixtureMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    local sq = PartMenu.squareOf(worldobjects)
    if not sq or test then return end
    local text, fault = FixtureMenu.lineOn(sq, player)
    if not text then return end
    local option = context:addOption(text, nil, nil)
    if fault then option.notAvailable = true else option.isDisabled = true end
end

Events.OnFillWorldObjectContextMenu.Add(FixtureMenu.fill)

return FixtureMenu
