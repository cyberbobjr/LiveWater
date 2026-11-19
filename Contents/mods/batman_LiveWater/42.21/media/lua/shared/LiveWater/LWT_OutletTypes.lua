-- LiveWater: registry of the consumers other mods add (ADR-012 D04), filled through
-- LiveWater.API.registerOutlet while files load. Pure, no game API. An outlet type names where the
-- water of an outlet goes (third result of the `outlet` hook); its handler is an object with
--   need(part)                     required: litres the outlet would take this step
--   deliver(part, litres, quality) required: the litres it was given (waterDelivered)
--   release(part)                  optional: the part left (pickup, removal)
--   cut(part)                      optional: a valve just kept the outlet from the water (ADR-010 D04)
-- (called with ":", the handler as self). LiveWater's own consumers (OWN: the house inlet, the
-- sprinklers, the drip lines, the barrel fittings) need the services of the authority: the
-- composition root registers them in LWT_Outlets under the same contract (OutletTypes.check), then
-- adopts every type registered here. Their names are taken.

local Check = require "LiveWater/LWT_Check"

local OutletTypes = {}
OutletTypes.__index = OutletTypes

-- Types of LiveWater's own consumers (server LWT_Server).
OutletTypes.OWN = { houseInlet = true, sprinkler = true, drip = true, barrelFill = true }

local REQUIRED = { "need", "deliver" }
local OPTIONAL = { "release", "cut" }

function OutletTypes.new()
    return setmetatable({ handlers = {}, sealed = false }, OutletTypes)
end

function OutletTypes.isType(v)
    return Check.isName(v) or Check.isNamespaced(v)
end

-- Does `handler` follow the contract above?
function OutletTypes.check(handler)
    if type(handler) ~= "table" then return false end
    for i = 1, #REQUIRED do
        if type(handler[REQUIRED[i]]) ~= "function" then return false end
    end
    for i = 1, #OPTIONAL do
        local fn = handler[OPTIONAL[i]]
        if fn ~= nil and type(fn) ~= "function" then return false end
    end
    return true
end

-- Returns true, or false and "registration_closed", "invalid_type", "invalid_handler",
-- "duplicate_outlet".
function OutletTypes:register(outletType, handler)
    if self.sealed then return false, "registration_closed" end
    if not OutletTypes.isType(outletType) then return false, "invalid_type" end
    if not OutletTypes.check(handler) then return false, "invalid_handler" end
    if OutletTypes.OWN[outletType] or self.handlers[outletType] then return false, "duplicate_outlet" end
    self.handlers[outletType] = handler
    return true
end

function OutletTypes:seal()
    self.sealed = true
end

-- Registered types, sorted, and their handlers by type.
function OutletTypes:all()
    local list = {}
    for name in pairs(self.handlers) do list[#list + 1] = name end
    table.sort(list)
    return list, self.handlers
end

return OutletTypes
