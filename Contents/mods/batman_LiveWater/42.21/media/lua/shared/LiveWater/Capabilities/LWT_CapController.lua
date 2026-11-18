-- LiveWater capability "controller": decides when a valve opens (ADR-001 D02, D19, D20).
--   mode     "manual" (default): only a player opens and closes the valve;
--            "timer": the part is also held open once per slice of `every` hours (slice number
--            floor(world hours / every) compared with the last one watered, never a minute test,
--            D09), for the time to serve its outlet: it stays open while the outlet is served,
--            and closes as soon as a step is not ("idle", no water, no pressure...)
--   every    hours between two openings of a timer (default 6); a player sets it on the part
--            within the sandbox bounds SprinklerTimerMin and SprinklerTimerMax (command setTimer)
--   watts    power a timer draws (default 5): an electric consumer (LWT_Power, D20); without
--            current it triggers nothing; opening the valve by hand stays possible
--   choices  hours offered in the menu (default 1, 2, 3, 4, 6, 8, 12, 24)
-- State: { every (set by a player, nil: as defined), slice (last slice watered), watering (held
-- open now), powered (current this step) }.
-- Revision 9: hooks prepare (start of a step), opens (held open), timer, setTimer.

local Check = require "LiveWater/LWT_Check"

local MAX_HOURS = 168
local DEFAULT_CHOICES = { 1, 2, 3, 4, 6, 8, 12, 24 }

local function isChoices(v)
    if type(v) ~= "table" or #v < 1 or #v > 12 then return false end
    for i = 1, #v do
        if not Check.isInteger(v[i], 1, MAX_HOURS) then return false end
    end
    return true
end

local SPEC = {
    mode = Check.oneOf({ manual = true, timer = true }, "manual"),
    every = Check.integer(1, MAX_HOURS, 6),
    watts = Check.number(0, 1000, 5),
    choices = { default = DEFAULT_CHOICES, valid = isChoices },
}

local Controller = {}

function Controller.define(params)
    local out, field = Check.fields(params, SPEC)
    if out then
        local copy = {}
        for i = 1, #out.choices do copy[i] = out.choices[i] end
        out.choices = copy
    end
    return out, field
end

local function isTimer(p)
    return p.mode == "timer"
end

local function every(p, d)
    return d and d.every or p.every
end

-- A timer needs current: a few watts, always (its clock runs).
function Controller.power(p)
    if not isTimer(p) or p.watts <= 0 then return nil end
    return true, p.watts
end

function Controller.powered(p, d, on)
    d.powered = on == true
end

-- Start of a step: a timer with current opens once per new slice of hours (ctx.hours: world age).
function Controller.prepare(p, d, ctx)
    if not isTimer(p) or d.powered == false or not (ctx and ctx.hours) then return end
    local slice = math.floor(ctx.hours / every(p, d))
    if slice ~= d.slice then
        d.slice = slice
        d.watering = true
    end
end

function Controller.opens(p, d)
    return isTimer(p) and d ~= nil and d.watering == true
end

function Controller.stepped(p, d, outcome)
    if d.watering then d.watering = outcome.outlet == "served" end
end

-- Hours between two openings of a timer, or nil.
function Controller.timer(p, d)
    if not isTimer(p) then return nil end
    return every(p, d)
end

function Controller.setTimer(p, d, hours)
    d.every = hours
end

function Controller.actions(p, d)
    if not isTimer(p) then return {} end
    local choices = {}
    for i = 1, #p.choices do
        choices[i] = { key = "ContextMenu_LWT_EveryHours", arg = p.choices[i], args = { hours = p.choices[i] } }
    end
    return { { command = "setTimer", key = "ContextMenu_LWT_SetTimer", choices = choices } }
end

function Controller.lines(p, d)
    if not isTimer(p) then return {} end
    local out = { { "IGUI_LWT_Timer_Every", every(p, d), rank = 12 } }
    if d and d.powered == false then out[2] = { "IGUI_LWT_Timer_NoPower", rank = 13 } end
    return out
end

return Controller
