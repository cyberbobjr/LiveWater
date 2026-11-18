-- LiveWater capability "outlet": the only place where water leaves the network (ADR-001 D13).
--   type          required name of the outlet ("houseInlet", "sprinkler", or a new one)
--   pressureCost  pressure the outlet takes from the budget (default by type, else 1)
--   needsClean    tainted water is refused without a filter (default by type, else false)
-- Defaults by type are data (D14, D17); any other type gets GENERIC.
-- State (revision 7): { state = what the last step did with it: "served", "idle", "closed",
-- "no_water", "unfiltered", "no_pressure" (LWT_Flow) }. An outlet that needs clean water looks
-- "unfiltered" after a step that refused tainted water, else "filtered" (house inlet sprites, D17).

local Check = require "LiveWater/LWT_Check"

-- `lines`: prefix of the translation key of the state line (key = prefix .. state).
local TYPES = {
    houseInlet = { pressureCost = 2, needsClean = true, lines = "IGUI_LWT_Outlet_" },
    sprinkler = { pressureCost = 1, needsClean = false, lines = "IGUI_LWT_Sprinkler_" },
}
local GENERIC = { pressureCost = 1, needsClean = false, lines = "IGUI_LWT_Outlet_" }

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

-- Pressure cost, "needs clean water" and (revision 7) the outlet type.
function Outlet.outlet(p)
    return p.pressureCost, p.needsClean, p.type
end

function Outlet.stepped(p, d, outcome)
    d.state = outcome.outlet
end

function Outlet.look(p, d)
    if not p.needsClean then return nil end
    if d and d.state == "unfiltered" then return "unfiltered" end
    return "filtered"
end

-- State line: key "<prefix of the type><state>" ("IGUI_LWT_Outlet_served", "IGUI_LWT_Sprinkler_idle").
function Outlet.lines(p, d)
    if not (d and d.state) then return {} end
    return { { (TYPES[p.type] or GENERIC).lines .. d.state, rank = 10 } }
end

return Outlet
