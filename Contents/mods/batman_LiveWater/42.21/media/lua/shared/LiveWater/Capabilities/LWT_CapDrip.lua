-- LiveWater capability "drip" (API revision 15): a part laid on the ground that waters the squares
-- beside it, those it is not linked to (ADR-004 D02; server LWT_Plants with LWT_DripArea). All its
-- water goes to the plants (D03), it makes no sound (D06). Served, each square draws its flow at
-- every step, thirsty plants or not; the plants beside it take what they need, the rest is lost
-- (ADR-006 D01).
--   dose  litres of one dose (default 0.2, the sprinkler's)
--   flow  optional (API revision 16, ADR-006 D02): litres drawn per square and per ten-minute step,
--         0..100; absent, the sandbox option DripFlow (0.5 by default)

local Check = require "LiveWater/LWT_Check"
local Settings = require "LiveWater/LWT_Settings"

local SPEC = {
    dose = Check.number(0.01, 100, 0.2),
    flow = { valid = function(v) return Check.isNumber(v, 0, 100) end },
}

local DEFAULT_FLOW = 0.5

local Drip = {}

function Drip.define(params)
    return Check.fields(params, SPEC)
end

-- Litres of a dose and litres drawn per step (its own flow, else the sandbox option).
function Drip.drip(p, d, ctx)
    return p.dose, p.flow or Settings.value(ctx, "DripFlow", DEFAULT_FLOW)
end

-- Information: litres drawn per line square and per ten minutes (ADR-006 D09).
function Drip.lines(p, d, ctx)
    local _, flow = Drip.drip(p, d, ctx)
    return { { "IGUI_LWT_Flow_Drip", Settings.litres(flow), rank = 14 } }
end

return Drip
