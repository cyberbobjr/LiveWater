-- LiveWater capability "fitting" (API revision 11): a barrel fitting between a pipe and a container
-- (ADR-001 D26, P02, P17). The player sets it to
--   "fill" (default): an outlet of type "barrelFill": the network fills the container, never more
--          than its free room (no leak), never another fluid than the one it holds;
--   "pump": a source: the pumps of the network draw the container's content instead of their own
--          intake (LWT_Flow), as long as it holds water (clean or tainted, vanilla rule: the house
--          tap purifies) or fuel.
--   rate   litres a step at most, both ways (default 50, a pond pump's flow)
-- What the container holds is sensed by the authority before each step (server LWT_Fittings,
-- `sense` hook): { found, shape ("tall" or "low"), fluid ("clean", "tainted", "fuel", "other", nil
-- when empty), amount, free, cx, cy, cz }.
-- State: { mode, found, shape, fluid, amount, free, cx, cy, cz, state = what the last step did }.

local Check = require "LiveWater/LWT_Check"

local SPEC = { rate = Check.number(0, 100000, 50) }
local MODES = { fill = true, pump = true }
local DRAWN = { clean = true, tainted = true, fuel = true }

local Fitting = {}

function Fitting.define(params)
    return Check.fields(params, SPEC)
end

local function mode(d)
    return d and d.mode or "fill"
end

-- What a container set to Fill holds: "any" when empty, "water", "fuel", or "other".
local function holds(d)
    if not d or not d.fluid then return "any" end
    if d.fluid == "fuel" then return "fuel" end
    if d.fluid == "clean" or d.fluid == "tainted" then return "water" end
    return "other"
end

-- Set to Fill it is an outlet: pressure cost 1, no clean water needed, type "barrelFill", and
-- (fourth result) the fluid its container takes.
function Fitting.outlet(p, d)
    if mode(d) ~= "fill" then return nil end
    return 1, false, "barrelFill", holds(d)
end

-- Set to Pump: litres the pumps may draw from the container and their quality.
function Fitting.draw(p, d)
    if mode(d) ~= "pump" or not (d and d.found) or not DRAWN[d.fluid] then return nil end
    return math.min(d.amount or 0, p.rate), d.fluid
end

function Fitting.sense(p, d, info)
    d.found = info.found == true
    d.shape, d.fluid, d.amount, d.free = info.shape, info.fluid, info.amount, info.free
    d.cx, d.cy, d.cz = info.cx, info.cy, info.cz
end

-- Mode, the sensed state (read only) and the rate.
function Fitting.fittingMode(p, d)
    return mode(d), d or {}, p.rate
end

function Fitting.setFittingMode(p, d, m)
    if MODES[m] then d.mode = m end
end

function Fitting.stepped(p, d, outcome)
    d.state = outcome.outlet
end

function Fitting.status(p, d)
    return d and d.state or nil
end

function Fitting.look(p, d)
    if mode(d) == "pump" then return "pump" end
    if d and d.shape == "low" then return "fill_low" end
    return "fill"
end

function Fitting.actions(p, d)
    if mode(d) == "fill" then return { { command = "switchFitting", key = "ContextMenu_LWT_FittingToPump" } } end
    return { { command = "switchFitting", key = "ContextMenu_LWT_FittingToFill" } }
end

function Fitting.lines(p, d)
    local out = { { "IGUI_LWT_Fitting_" .. mode(d), rank = 5 } }
    if not (d and d.found) then
        out[#out + 1] = { "IGUI_LWT_Fitting_NoBarrel", rank = 6 }
    else
        out[#out + 1] = { "IGUI_LWT_Fitting_Content", math.floor((d.amount or 0) + 0.5), rank = 6 }
        if d.fluid then out[#out + 1] = { "IGUI_LWT_Fluid_" .. d.fluid, rank = 7 } end
    end
    if d and d.state and mode(d) == "fill" then out[#out + 1] = { "IGUI_LWT_Fitting_" .. d.state, rank = 10 } end
    return out
end

return Fitting
