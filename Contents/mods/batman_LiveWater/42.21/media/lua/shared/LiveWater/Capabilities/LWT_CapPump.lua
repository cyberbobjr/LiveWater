-- LiveWater capability "pump": puts the network under pressure (ADR-001 D14-D16, Q03).
--   ports     pipes that may leave the part, 1..4 (default 4)
--   pressure  pressure budget given to the network (default 6)
--   flow      litres per ten-minute step (default 50: 5 L per game minute)

local Check = require "LiveWater/LWT_Check"

local SPEC = {
    ports = Check.integer(1, 4, 4),
    pressure = Check.number(0, 1000, 6),
    flow = Check.number(0, 100000, 50),
}

local Pump = {}

function Pump.define(params)
    return Check.fields(params, SPEC)
end

return Pump
