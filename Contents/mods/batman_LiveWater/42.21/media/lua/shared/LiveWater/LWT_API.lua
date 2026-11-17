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

-- Starting capability kinds (D02): kind -> file under LiveWater/Capabilities.
local STARTING_CAPABILITIES = {
    conduit = "LWT_CapConduit",
    intake = "LWT_CapIntake",
    pump = "LWT_CapPump",
    valve = "LWT_CapValve",
    filter = "LWT_CapFilter",
    outlet = "LWT_CapOutlet",
    controller = "LWT_CapController",
}

LiveWater = LiveWater or {}

local capabilities = Capabilities.new()
for kind, file in pairs(STARTING_CAPABILITIES) do
    capabilities:register(kind, require("LiveWater/Capabilities/" .. file))
end
local parts = Parts.new(capabilities)

-- Internal to LiveWater (not the public API): the catalog the domain and adapters use.
LiveWater.Capabilities = capabilities
LiveWater.Parts = parts
LiveWater.Events = EventBus.new(EventBus.NAMES)

local API = { revision = 1 }
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

-- Copy of the checked definition of a part type, or nil.
function API.part(id)
    return parts:describe(id)
end

Events.OnInitGlobalModData.Add(function()
    capabilities:seal()
    parts:seal()
end)

return API
