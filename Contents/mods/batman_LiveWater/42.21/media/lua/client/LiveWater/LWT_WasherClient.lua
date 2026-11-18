-- LiveWater: client side of the washing machine fix (ADR-001 L13, Q08; server LWT_WasherFix). A
-- plain washer the server marked as plumbed (ModData LiveWaterWasher, only washers fed by
-- LiveWater's relays) takes that state locally, since 42.22 never sends it (IsoClothingWasher
-- .saveChange). Applied when the player looks at the washer: its right-click menu and the switch
-- of its container window (the vanilla handler is wrapped, arguments and result kept). Off when
-- the sandbox option WasherFix is off.

require "LiveWater/LWT_API"
require "ISUI/LootWindow/Handlers/ClothingWasherToggle"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local PartMenu = require "LiveWater/LWT_PartMenu"

local WasherClient = {}

WasherClient.KEY = WaterObjects.WASHER_KEY

local function enabled()
    local vars = SandboxVars and SandboxVars.LiveWater
    return not (vars and vars.WasherFix == false)
end

function WasherClient.apply(obj)
    if not enabled() or not obj or not instanceof(obj, "IsoClothingWasher") then return end
    if WaterObjects.mark(obj, WasherClient.KEY) and not obj:getUsesExternalWaterSource() then
        obj:setUsesExternalWaterSource(true)
    end
end

function WasherClient.fill(playerNum, context, worldobjects, test)
    local sq = PartMenu.squareOf(worldobjects)
    if not sq then return end
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do WasherClient.apply(objects:get(i)) end
end

local Handler = ISLootWindowObjectControlHandler_ClothingWasherToggle
if Handler then
    local original = Handler.shouldBeVisible
    function Handler:shouldBeVisible(...)
        WasherClient.apply(self.object)
        return original(self, ...)
    end
end

Events.OnFillWorldObjectContextMenu.Add(WasherClient.fill)

return WasherClient
