-- LiveWater capability "pump": puts the network under pressure (ADR-001 D14-D16, D20, Q03).
--   ports     pipes that may leave the part, 1..4 (default 4)
--   pressure  pressure budget given to the network (default 6)
--   flow      litres per ten-minute step (default 50: 5 L per game minute), times the sandbox
--             option PumpFlowMultiplier
--   watts     power drawn while running (default 250; 0 = needs no current)
-- State: { powered = current this step (nil: never asked), running = gave water last step,
--          litres = its share of the water delivered last step }.
-- A pump gives nothing without current; it runs only while an outlet takes water (auto-stop).

local Check = require "LiveWater/LWT_Check"
local Settings = require "LiveWater/LWT_Settings"

local SPEC = {
    ports = Check.integer(1, 4, 4),
    pressure = Check.number(0, 1000, 6),
    flow = Check.number(0, 100000, 50),
    watts = Check.number(0, 100000, 250),
}

local Pump = {}

function Pump.define(params)
    return Check.fields(params, SPEC)
end

-- Can the pump work now?
local function works(p, d)
    return not (d and d.powered == false)
end

local function running(d)
    return d ~= nil and d.running == true
end

function Pump.pressurizes()
    return true
end

function Pump.ports(p)
    return p.ports
end

function Pump.supply(p, d, ctx)
    if not works(p, d) then return 0, 0 end
    return p.pressure, p.flow * Settings.scale(ctx, "PumpFlowMultiplier")
end

function Pump.power(p, d)
    return p.watts > 0, running(d) and p.watts or 0
end

function Pump.powered(p, d, on)
    d.powered = on == true
end

function Pump.stepped(p, d, outcome)
    d.running = works(p, d) and outcome.through > 0
    d.litres = d.running and outcome.through or 0
end

function Pump.output(p, d)
    return d and d.litres or 0
end

function Pump.look(p, d)
    return running(d) and "on" or "off"
end

-- State line, then flow.
function Pump.lines(p, d)
    local state = "IGUI_LWT_Pump_Standby"
    if running(d) then
        state = "IGUI_LWT_Pump_Running"
    elseif not works(p, d) then
        state = "IGUI_LWT_Pump_NoPower"
    end
    return {
        { state, rank = 10 },
        { "IGUI_LWT_Pump_Flow", math.floor((d and d.litres or 0) + 0.5), rank = 20 },
    }
end

return Pump
