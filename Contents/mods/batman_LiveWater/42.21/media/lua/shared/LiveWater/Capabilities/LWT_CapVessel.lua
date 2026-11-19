-- LiveWater capability "vessel" (API revision 21, ADR-011): the part draws water from a container
-- set against it, on one of its four sides (a pond pump against a barrel; revision 23, ADR-014 D01:
-- or against a gas station fuel pump, whose gasoline it draws). It always draws: the
-- authority senses the container (server LWT_Fittings: `sense`, `container` = "draw", the amount
-- shared with the others drawing from it, count while away), and the pump gives that water before
-- its own source (LWT_Flow, D03); no other pump draws from it.
--   rate   litres a step at most (default 50, a pond pump's flow)
-- Water (clean or tainted, kept as it is: D02) or fuel (revision 23), never another fluid.
-- State: { found, shape, fluid, amount, free, share, cx, cy, cz, offline } (LWT_Sensed).

local Check = require "LiveWater/LWT_Check"
local Sensed = require "LiveWater/LWT_Sensed"

local SPEC = { rate = Check.number(0, 100000, 50) }
local WATER = { clean = true, tainted = true }
local DRAWN = { clean = true, tainted = true, fuel = true }

local Vessel = {}

function Vessel.define(params)
    return Check.fields(params, SPEC)
end

function Vessel.sense(p, d, info)
    Sensed.record(d, info)
end

-- What LWT_Fittings does with the container: "draw", the sensed state (read only), the rate.
function Vessel.container(p, d)
    return "draw", d or {}, p.rate
end

function Vessel.draw(p, d)
    if not (d and d.found) or not DRAWN[d.fluid] then return nil end
    return math.min(d.share or d.amount or 0, p.rate), d.fluid
end

-- The barrel against it and the water it holds (D04); fuel (a fuel pump, a barrel of gasoline): what
-- it holds and its fluid (ADR-014 D01); nothing without a container (a pond pump alone).
function Vessel.lines(p, d)
    if not (d and d.found) then return {} end
    local litres = math.floor((d.amount or 0) + 0.5)
    if d.fluid == nil or WATER[d.fluid] then return { { "IGUI_LWT_Vessel_Content", litres, rank = 41 } } end
    if d.fluid == "fuel" then
        return { { "IGUI_LWT_Vessel_Tank", litres, rank = 41 }, { "IGUI_LWT_Fluid_fuel", rank = 42 } }
    end
    return {}
end

return Vessel
