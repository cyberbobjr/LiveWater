-- LiveWater capability "pump": puts the network under pressure (ADR-001 D14-D16, D20, D24, Q03).
--   ports            pipes that may leave the part, 1..4 (default 4)
--   pressure         pressure budget given to the network (default 6)
--   flow             litres per ten-minute step at full efficiency (default 50: 5 L per game
--                    minute), times the sandbox option PumpFlowMultiplier
--   watts            power drawn while running (default 250; 0 = needs no current)
--   wear             efficiency points lost per running minute (default 0.01: about a week of
--                    running from 100 to 0), times the sandbox option PumpWearMultiplier (P04)
--   breakdownBelow   efficiency under which it may break down (default 20)
--   breakdownChance  chance of a breakdown per running step under that (default 0.02)
--   repairItem       full type of the material of a repair (default "Base.ScrapMetal", P05)
--   repairCount      how many (default 2)
--   repairTool       optional item tag of the tool of a repair ("base:wrench")
--   sound            sound loop played while running (default "GeneratorLoop", P15)
--   noiseRadius, noiseVolume  noise zombies hear each running step (default 20, 20)
-- State: { on = switch (nil: on), powered = current this step (nil: never asked), running = gave
--          water last step, litres = its share of the water delivered last step, efficiency
--          (nil: 100), broken = stopped by a breakdown until repaired }.
-- A pump works when switched on, powered, not broken and above 0 %; it runs only while an
-- outlet takes water (auto-stop). A breakdown only stops it (Q05: no fire).

local Check = require "LiveWater/LWT_Check"
local Settings = require "LiveWater/LWT_Settings"

local function isFullType(v)
    return type(v) == "string" and #v <= 120 and string.match(v, "^%a[%w_]*%.%a[%w_]*$") ~= nil
end

local function isTag(v)
    return type(v) == "string" and #v <= 120 and string.match(v, "^%a[%w_]*:%a[%w_]*$") ~= nil
end

local SPEC = {
    ports = Check.integer(1, 4, 4),
    pressure = Check.number(0, 1000, 6),
    flow = Check.number(0, 100000, 50),
    watts = Check.number(0, 100000, 250),
    wear = Check.number(0, 100, 0.01),
    breakdownBelow = Check.number(0, 100, 20),
    breakdownChance = Check.number(0, 1, 0.02),
    repairItem = { default = "Base.ScrapMetal", valid = isFullType },
    repairCount = Check.integer(1, 100, 2),
    repairTool = { valid = isTag },
    sound = { default = "GeneratorLoop", valid = Check.isName },
    noiseRadius = Check.integer(0, 100, 20),
    noiseVolume = Check.integer(0, 100, 20),
}

local MINUTES_PER_STEP = 10
local FULL = 100

local Pump = {}

function Pump.define(params)
    return Check.fields(params, SPEC)
end

local function efficiency(d)
    return d and d.efficiency or FULL
end

local function switchedOn(d)
    return not (d and d.on == false)
end

-- Can the pump work now?
local function works(p, d)
    return switchedOn(d) and not (d and d.powered == false) and not (d and d.broken) and efficiency(d) > 0
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
    return p.pressure, p.flow * efficiency(d) / FULL * Settings.scale(ctx, "PumpFlowMultiplier")
end

function Pump.power(p, d)
    return p.watts > 0, running(d) and p.watts or 0
end

function Pump.powered(p, d, on)
    d.powered = on == true
end

-- Wear of a running step, then maybe a breakdown (P04).
local function wear(p, d, ctx)
    local left = math.max(0, efficiency(d) - p.wear * MINUTES_PER_STEP * Settings.scale(ctx, "PumpWearMultiplier"))
    d.efficiency = left
    if left <= 0 then
        d.broken = true
    elseif left < p.breakdownBelow and ctx and ctx.random and ctx.random() < p.breakdownChance then
        d.broken = true
    end
end

function Pump.stepped(p, d, outcome, ctx)
    d.running = works(p, d) and outcome.through > 0
    d.litres = d.running and outcome.through or 0
    if d.running then wear(p, d, ctx) end
end

function Pump.output(p, d)
    return d and d.litres or 0
end

function Pump.look(p, d)
    return running(d) and "on" or "off"
end

-- Switch (P03): current position, and the change (a pump switched off stops at once).
function Pump.switchable(p, d)
    return switchedOn(d)
end

function Pump.switch(p, d, on)
    d.on = on == true
    if not d.on then
        d.running = false
        d.litres = 0
    end
end

-- Repair (P05): material, count, tool tag, and why it cannot be done now ("running",
-- "not_needed") or nil.
function Pump.repairable(p, d)
    local why = nil
    if running(d) then
        why = "running"
    elseif efficiency(d) >= FULL and not (d and d.broken) then
        why = "not_needed"
    end
    return p.repairItem, p.repairCount, p.repairTool, why
end

function Pump.repair(p, d)
    d.efficiency = FULL
    d.broken = false
end

function Pump.sound(p, d)
    if not running(d) then return nil end
    return p.sound, p.noiseRadius, p.noiseVolume
end

local function stateKey(p, d)
    if d and d.broken then return "IGUI_LWT_Pump_Broken" end
    if not switchedOn(d) then return "IGUI_LWT_Pump_Off" end
    if running(d) then return "IGUI_LWT_Pump_Running" end
    if d and d.powered == false then return "IGUI_LWT_Pump_NoPower" end
    return "IGUI_LWT_Pump_Standby"
end

-- State, flow, efficiency (P08).
function Pump.lines(p, d)
    return {
        { stateKey(p, d), rank = 10 },
        { "IGUI_LWT_Pump_Flow", math.floor((d and d.litres or 0) + 0.5), rank = 20 },
        { "IGUI_LWT_Pump_Efficiency", math.floor(efficiency(d) + 0.5), rank = 25 },
    }
end

function Pump.actions(p, d)
    local list = {}
    if switchedOn(d) then
        list[1] = { command = "switchPump", key = "ContextMenu_LWT_TurnOff" }
    else
        list[1] = { command = "switchPump", key = "ContextMenu_LWT_TurnOn" }
    end
    local _, _, _, why = Pump.repairable(p, d)
    if not why then list[2] = { command = "repairPump", key = "ContextMenu_LWT_Repair", item = p.repairItem } end
    return list
end

return Pump
