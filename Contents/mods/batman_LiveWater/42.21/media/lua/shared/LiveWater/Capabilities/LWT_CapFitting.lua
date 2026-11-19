-- LiveWater capability "fitting" (API revision 11; Fill only since revision 22, ADR-012 D02): a barrel
-- fitting between a pipe and a container (ADR-001 D26, P02, P17). It is a consumer, an outlet of type
-- "barrelFill": the network fills the container, never more than its free room (no leak), never
-- another fluid than the one it holds; water of any quality, the container receives it tainted
-- (ADR-005 D07, server LWT_Fittings). To send a barrel's water into the pipes, a pump stands against
-- it (capability "vessel", ADR-011).
--   rate   litres a step at most (default 50, a pond pump's flow)
-- What the container holds is sensed by the authority before each step (server LWT_Fittings,
-- `sense` hook): { found, shape ("tall" or "low"), fluid ("clean", "tainted", "fuel", "other", nil
-- when empty), amount, free, cx, cy, cz, offline (optional: what the network put in the container
-- while its square was not loaded, not yet written to the real container: { added, quality },
-- ADR-006 D06) } (LWT_Sensed).
-- A container may refuse water for now (`blocked`: "feed", a vanilla feeding trough holding feed has no
-- water tank, ADR-013 D04): its free room is 0 and the information says why.
-- The fitting never mixes (ADR-014 D04): an empty container takes any fluid carried, one holding water
-- takes water, one holding fuel takes fuel; a container that takes water even empty (`takes`, a
-- feeding trough: the game's whitelist is water and tainted water) never takes another fluid.
-- State: { found, shape, fluid, amount, free, cx, cy, cz, offline, blocked, takes, state = what the
-- last step did }.

local Check = require "LiveWater/LWT_Check"
local Sensed = require "LiveWater/LWT_Sensed"

local SPEC = { rate = Check.number(0, 100000, 50) }

local Fitting = {}

function Fitting.define(params)
    return Check.fields(params, SPEC)
end

-- What the container takes: what it holds ("water", "fuel", "other"), never mixed; empty, what it
-- takes even empty (`takes`: "water" for a feeding trough, ADR-014 D04), else "any".
local function holds(d)
    if not d then return "any" end
    if not d.fluid then return d.takes or "any" end
    if d.fluid == "fuel" then return "fuel" end
    if d.fluid == "clean" or d.fluid == "tainted" then return "water" end
    return "other"
end

-- An outlet: pressure cost 1, never clean water needed (ADR-005 D07), type "barrelFill", and
-- (fourth result) the fluid its container takes.
function Fitting.outlet(p, d)
    return 1, false, "barrelFill", holds(d)
end

function Fitting.sense(p, d, info)
    Sensed.record(d, info)
end

-- What LWT_Fittings does with the container: "fill", the sensed state (read only), the rate.
function Fitting.container(p, d)
    return "fill", d or {}, p.rate
end

function Fitting.stepped(p, d, outcome)
    d.state = outcome.outlet
end

function Fitting.status(p, d)
    return d and d.state or nil
end

function Fitting.look(p, d)
    if d and d.shape == "low" then return "fill_low" end
    return "fill"
end

-- Translation key of the reason a container refuses water (ADR-013 D04).
local BLOCKED = { feed = "IGUI_LWT_Fitting_TroughFeed" }

-- State line: "IGUI_LWT_Fitting_<state>"; a fluid refused by a container of water: "this is not
-- water" (ADR-014 D03).
local function stateKey(d)
    if d.state == "wrong_fluid" and holds(d) == "water" then return "IGUI_LWT_Fitting_NotWater" end
    return "IGUI_LWT_Fitting_" .. d.state
end

function Fitting.lines(p, d)
    if d and d.found and d.blocked then
        return { { BLOCKED[d.blocked] or "IGUI_LWT_Fitting_idle", rank = 6 } }
    end
    local out = {}
    if not (d and d.found) then
        out[#out + 1] = { "IGUI_LWT_Fitting_NoBarrel", rank = 6 }
    else
        out[#out + 1] = { "IGUI_LWT_Fitting_Content", math.floor((d.amount or 0) + 0.5), rank = 6 }
        if d.fluid then out[#out + 1] = { "IGUI_LWT_Fluid_" .. d.fluid, rank = 7 } end
    end
    if d and d.state then out[#out + 1] = { stateKey(d), rank = 10 } end
    return out
end

return Fitting
