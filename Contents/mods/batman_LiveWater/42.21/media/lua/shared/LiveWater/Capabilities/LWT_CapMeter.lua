-- LiveWater capability "meter": records the water that went through the part (ADR-001 D24, P12;
-- ADR-008 D03). No params. State: { litres = litres through it during the last step, quality =
-- quality of that water ("clean", "tainted"), nil when none went through, total = litres through it
-- since it was set down (nil: 0) }. The total lives in the mirrored state, so a meter picked up and
-- set down again keeps it, like a real one; it is never reset. The fluid is always water for now
-- (a fuel network, D26, will add its own lines).

local Check = require "LiveWater/LWT_Check"

local Meter = {}

function Meter.define(params)
    return Check.fields(params, {})
end

function Meter.stepped(p, d, outcome)
    d.litres = outcome.through
    d.quality = outcome.through > 0 and outcome.quality or nil
    d.total = (d.total or 0) + outcome.through
end

-- Flow of the last step, then the fluid when some went through.
function Meter.lines(p, d)
    local litres = d and d.litres or 0
    local list = { { "IGUI_LWT_Meter_Flow", math.floor(litres + 0.5), rank = 20 } }
    if litres > 0 and d.quality then
        list[2] = { "IGUI_LWT_Meter_Water_" .. d.quality, rank = 30 }
    end
    return list
end

-- "Information" opens the water meter window: rolling digits of the whole litres since set down.
function Meter.panel(p, d)
    return "counter", "IGUI_LWT_Window_Meter", math.floor(d and d.total or 0)
end

return Meter
