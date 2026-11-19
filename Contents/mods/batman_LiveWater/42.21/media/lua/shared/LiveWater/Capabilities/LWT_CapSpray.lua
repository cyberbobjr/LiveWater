-- LiveWater capability "spray" (API revision 8): the part waters the plants around it with the water
-- its outlet receives (ADR-001 D19, P13, P14). The server's plants service (LWT_Plants, outlet type
-- "sprinkler") asks it how far, by how much and how much it draws: open, it draws its flow at every
-- step, thirsty plants or not; the plants take what they need, the rest is lost (ADR-006 D01).
--   radius     squares around the part on each axis (square, ADR-003 D01), 0..10 (default 2, D19), times the sandbox option
--              SprinklerRadiusMultiplier, rounded
--   dose       litres of one watering dose (default 0.2: the vanilla 200 ml per use,
--              ZomboidGlobals.farmingFluidContainerMillilitresPerUse)
--   jetSheet   optional sprite name prefix of the animated jet drawn by the clients while it sprays
--              (D08a); frame f (0..jetFrames-1), facing k (0..3: S, E, N, W) is
--              jetSheet .. (jetFirst + 4 * f + k)
--   jetFirst   index of the first jet sprite (default 0)
--   jetFrames  number of jet frames, 1..12 (default 6)
--   sound      optional (API revision 13): sound script looped for the players while it sprays
--              (P14; LiveWater's sprinklers: the vanilla watering sound "WaterCrops")
--   loss       optional (API revision 15, ADR-004 D03): share of the water drawn lost in the air,
--              0..1 (default 0.25: of 10 L drawn, 7.5 L can reach the plants; ADR-006 D02)
--   flow       optional (API revision 16, ADR-006 D02): litres drawn per ten-minute step while it is
--              open, 0..1000; absent, the sandbox option SprinklerFlow (10 by default)
--   noiseRadius, noiseVolume  optional (API revision 15, ADR-004 D06): what zombies hear at each
--              step while it sprays with a sound (default 10, 10)
-- State: { on = water came out at the last step }.

local Check = require "LiveWater/LWT_Check"
local Settings = require "LiveWater/LWT_Settings"

local function isPrefix(v)
    return type(v) == "string" and #v > 0 and #v <= 64 and string.match(v, "^[%w_]+$") ~= nil
end

local SPEC = {
    radius = Check.integer(0, 10, 2),
    dose = Check.number(0.01, 10, 0.2),
    jetSheet = { valid = isPrefix },
    jetFirst = Check.integer(0, 10000, 0),
    jetFrames = Check.integer(1, 12, 6),
    sound = { valid = Check.isName },
    loss = Check.number(0, 1, 0.25),
    noiseRadius = Check.integer(0, 100, 10),
    noiseVolume = Check.integer(0, 100, 10),
    flow = { valid = function(v) return Check.isNumber(v, 0, 1000) end },
}

local DEFAULT_FLOW = 10

local MAX_RADIUS = 10

local Spray = {}

function Spray.define(params)
    return Check.fields(params, SPEC)
end

local function spraying(d)
    return d ~= nil and d.on == true
end

-- Radius (scaled, rounded), litres of a dose, share of water lost in the air and litres drawn per
-- step (its own flow, else the sandbox option).
function Spray.spray(p, d, ctx)
    local radius = math.floor(p.radius * Settings.scale(ctx, "SprinklerRadiusMultiplier") + 0.5)
    return math.min(radius, MAX_RADIUS), p.dose, p.loss, p.flow or Settings.value(ctx, "SprinklerFlow", DEFAULT_FLOW)
end

-- Information: litres drawn per ten minutes and litres that reach the plants (ADR-006 D09).
function Spray.lines(p, d, ctx)
    local _, _, loss, flow = Spray.spray(p, d, ctx)
    return { { "IGUI_LWT_Flow_Spray", Settings.litres(flow), Settings.litres(flow * (1 - (loss or 0))), rank = 14 } }
end

function Spray.stepped(p, d, outcome)
    d.on = outcome.outlet == "served"
end

function Spray.look(p, d)
    return spraying(d) and "on" or "off"
end

-- Sound loop while it sprays (Publisher, the same state change as the jet): name, and the noise
-- zombies hear at each step (ADR-004 D06).
function Spray.sound(p, d)
    if not (p.sound and spraying(d)) then return nil end
    return p.sound, p.noiseRadius, p.noiseVolume
end

-- Jet frames (sheet, first index, frame count) and whether it sprays now; nil without a jet.
function Spray.jet(p, d)
    if not p.jetSheet then return nil end
    return p.jetSheet, p.jetFirst, p.jetFrames, spraying(d)
end

return Spray
