-- LiveWater capability "outlet": the only place where water leaves the network (ADR-001 D13).
--   type          required name of the outlet ("houseInlet", "sprinkler", or a new one: a name or
--                 "<Mod>:<Name>" whose handler a mod registers, LiveWater.API.registerOutlet)
--   pressureCost  pressure the outlet takes from the budget (default by type, else 1)
--   needsClean    tainted water is refused without a filter (default by type, else false)
--   costGroup     optional name (API revision 15): the outlets of a network with the same group pay
--                 their pressure cost once per step, together (default by type: "drip", ADR-004 D04)
--   takes         the fluid it takes (API revision 23, ADR-014 D03): "water" (default: clean or
--                 tainted), "fuel", "other" or "any"; another fluid is never delivered to it (state
--                 "wrong_fluid")
-- Defaults by type are data (D14, D17); any other type gets GENERIC. The house inlet and irrigation
-- (sprinkler, drip) take any water, clean or tainted, and no other fluid (ADR-005 D03, ADR-014 D03);
-- a consumer of another mod without `takes` takes water only.
-- State (revision 7): { state = what the last step did with it: "served", "idle", "closed",
-- "no_water", "unfiltered", "no_pressure", "wrong_fluid" (LWT_Flow) }. An outlet that needs clean water looks
-- "unfiltered" after a step that refused tainted water, else "filtered" (house inlet sprites, D17).

local Check = require "LiveWater/LWT_Check"

-- `lines`: prefix of the translation key of the state line (key = prefix .. state).
local TYPES = {
    houseInlet = { pressureCost = 2, needsClean = true, takes = "water", lines = "IGUI_LWT_Outlet_" },
    sprinkler = { pressureCost = 1, needsClean = false, takes = "water", lines = "IGUI_LWT_Sprinkler_" },
    drip = { pressureCost = 1, needsClean = false, costGroup = "drip", takes = "water", lines = "IGUI_LWT_Drip_" },
}
local GENERIC = { pressureCost = 1, needsClean = false, takes = "water", lines = "IGUI_LWT_Outlet_" }
local FLUIDS = { water = true, fuel = true, other = true, any = true }

local Outlet = {}

function Outlet.define(params)
    if type(params) ~= "table" or not (Check.isName(params.type) or Check.isNamespaced(params.type)) then
        return nil, "type"
    end
    local defaults = TYPES[params.type] or GENERIC
    local out, field = Check.fields(params, {
        pressureCost = Check.number(0, 1000, defaults.pressureCost),
        needsClean = Check.boolean(defaults.needsClean),
        costGroup = { default = defaults.costGroup, valid = Check.isName },
        takes = Check.oneOf(FLUIDS, defaults.takes),
    })
    if out then out.type = params.type end
    return out, field
end

-- Pressure cost, "needs clean water", (revision 7) the outlet type and (revision 23) the fluid it takes.
function Outlet.outlet(p)
    return p.pressureCost, p.needsClean, p.type, p.takes
end

-- Group whose outlets pay their pressure cost once per step together, or nil (revision 15).
function Outlet.costGroup(p)
    return p.costGroup
end

function Outlet.stepped(p, d, outcome)
    d.state = outcome.outlet
end

-- State of the last step (network view, E13), or nil.
function Outlet.status(p, d)
    return d and d.state or nil
end

function Outlet.look(p, d)
    if not p.needsClean then return nil end
    if d and d.state == "unfiltered" then return "unfiltered" end
    return "filtered"
end

-- State line: key "<prefix of the type><state>" ("IGUI_LWT_Outlet_served", "IGUI_LWT_Sprinkler_idle");
-- a refused fluid says "this is not water" for a water consumer (the prefix key), else "wrong liquid".
function Outlet.lines(p, d)
    if not (d and d.state) then return {} end
    if d.state == "wrong_fluid" and p.takes ~= "water" then return { { "IGUI_LWT_Outlet_WrongLiquid", rank = 10 } } end
    return { { (TYPES[p.type] or GENERIC).lines .. d.state, rank = 10 } }
end

return Outlet
