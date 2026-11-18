-- LiveWater: public API facade and composition root of the registries (ADR-001 D01-D07).
-- Register from a shared Lua file while files load, before OnInitGlobalModData:
--   LiveWater.API.registerCapability("meter", { define = function(params) return {} end })
--   LiveWater.API.registerPart("MyMod:PipeCopper", {
--       sprites = { [0] = "mymod_pipes_0", ..., [15] = "mymod_pipes_15" },
--       capabilities = { conduit = true } })
-- Every refusal returns false and a reason string, and prints an English warning.
-- Revisions only add functions or optional fields (D05).

local Capabilities = require "LiveWater/LWT_Capabilities"
local Parts = require "LiveWater/LWT_Parts"
local EventBus = require "LiveWater/LWT_Events"
local Sources = require "LiveWater/LWT_Sources"

-- Starting capability kinds (D02): kind -> file under LiveWater/Capabilities.
local STARTING_CAPABILITIES = {
    conduit = "LWT_CapConduit",
    intake = "LWT_CapIntake",
    pump = "LWT_CapPump",
    valve = "LWT_CapValve",
    filter = "LWT_CapFilter",
    outlet = "LWT_CapOutlet",
    controller = "LWT_CapController",
    layable = "LWT_CapLayable",
    meter = "LWT_CapMeter",
    spray = "LWT_CapSpray",
}

-- Starting source kinds (D16, D17): kind -> file under LiveWater/Sources.
local STARTING_SOURCES = {
    water = "LWT_SourceNaturalWater",
    well = "LWT_SourceWell",
}

LiveWater = LiveWater or {}

local capabilities = Capabilities.new()
for kind, file in pairs(STARTING_CAPABILITIES) do
    capabilities:register(kind, require("LiveWater/Capabilities/" .. file))
end
local parts = Parts.new(capabilities)
local sources = Sources.new()
for kind, file in pairs(STARTING_SOURCES) do
    sources:register(kind, require("LiveWater/Sources/" .. file))
end

-- Internal to LiveWater (not the public API): the catalog the domain and adapters use.
LiveWater.Capabilities = capabilities
LiveWater.Parts = parts
LiveWater.Sources = sources
LiveWater.Events = EventBus.new(EventBus.NAMES)

-- Revision 2: part definition field `variants`, capability hooks look, attach, power, powered,
-- stepped, output, lines (LWT_Parts.lua, LWT_Capabilities.lua).
-- Revision 3: filter capability field `item` (removable cartridge), hooks cartridge, fit, unfit,
-- actions.
-- Revision 4: pump fields wear, breakdownBelow, breakdownChance, repairItem, repairCount,
-- repairTool, sound, noiseRadius, noiseVolume; hooks switchable, switch, repairable, repair, sound.
-- Revision 5: capability "meter", conduit field `ports`, outcome.quality of `stepped` per part.
-- Revision 6: registerSource; the intake reports the quality of the source kind it recorded.
-- Revision 7: the `outlet` hook also gives the outlet type; outcome.outlet of `stepped` (what the
-- step did with an outlet); the outlet keeps it as its state, its look and its information line.
-- Revision 8: capability "spray" (radius, dose, jet frames; hooks spray, jet), valve hooks opened,
-- open, actions, lines; event valveChanged emitted when a player opens or closes a valve.
-- Revision 9: controller timer (fields every, watts, choices; hooks prepare, opens, timer,
-- setTimer), Parts:closed, action `choices`, ctx.hours of the step.
-- Revision 10: hook status (network view), commands showNetwork and network.
local API = { revision = 10 }
LiveWater.API = API

local function answer(call, id, ok, reason, detail)
    if ok then return true end
    print("LiveWater: " .. call .. "(" .. tostring(id) .. ") refused: " .. tostring(reason)
        .. (detail and (" (" .. tostring(detail) .. ")") or ""))
    return false, reason
end

-- Returns true, or false and a reason (see LWT_Parts.lua).
function API.registerPart(id, definition)
    return answer("registerPart", id, parts:register(id, definition))
end

-- Returns true, or false and a reason (see LWT_Capabilities.lua).
function API.registerCapability(kind, implementation)
    return answer("registerCapability", kind, capabilities:register(kind, implementation))
end

-- New kind of water source an intake can draw from (revision 6), see LWT_Sources.lua:
--   LiveWater.API.registerSource("MyMod:Cistern", { quality = "clean", sprites = { "my_tiles_0" } })
-- Returns true, or false and "registration_closed", "invalid_kind", "duplicate_source",
-- "invalid_definition".
function API.registerSource(kind, definition)
    return answer("registerSource", kind, sources:register(kind, definition))
end

-- Copy of the checked definition of a part type, or nil.
function API.part(id)
    return parts:describe(id)
end

Events.OnInitGlobalModData.Add(function()
    capabilities:seal()
    parts:seal()
    sources:seal()
end)

return API
