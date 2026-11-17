-- LiveWater capability "outlet": the only place where water leaves the network (ADR-001 D13).
--   type          required name of the outlet ("houseInlet", "sprinkler", or a new one)
--   pressureCost  pressure the outlet takes from the budget (default by type, else 1)
--   needsClean    tainted water is refused without a filter (default by type, else false)
-- Defaults by type are data (D14, D17); any other type gets GENERIC.

local Check = require "LiveWater/LWT_Check"

local TYPES = {
    houseInlet = { pressureCost = 2, needsClean = true },
    sprinkler = { pressureCost = 1, needsClean = false },
}
local GENERIC = { pressureCost = 1, needsClean = false }

local Outlet = {}

function Outlet.define(params)
    if type(params) ~= "table" or not Check.isName(params.type) then return nil, "type" end
    local defaults = TYPES[params.type] or GENERIC
    local out, field = Check.fields(params, {
        pressureCost = Check.number(0, 1000, defaults.pressureCost),
        needsClean = Check.boolean(defaults.needsClean),
    })
    if out then out.type = params.type end
    return out, field
end

function Outlet.outlet(p)
    return p.pressureCost, p.needsClean
end

return Outlet
