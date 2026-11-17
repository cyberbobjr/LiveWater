-- LiveWater capability "intake": the part takes water from a source (ADR-001 D16, D17).
--   quality  "tainted" (lake, pond, river: default) or "clean"

local Check = require "LiveWater/LWT_Check"

local SPEC = { quality = Check.oneOf({ clean = true, tainted = true }, "tainted") }

local Intake = {}

function Intake.define(params)
    return Check.fields(params, SPEC)
end

-- Extension point (D16): the source may run dry later (frost, empty well); always available now.
local function available(p, d, ctx)
    return true
end

function Intake.source(p, d, ctx)
    if available(p, d, ctx) then return p.quality end
    return nil
end

return Intake
