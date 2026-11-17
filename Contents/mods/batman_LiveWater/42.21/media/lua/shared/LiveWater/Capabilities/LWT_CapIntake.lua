-- LiveWater capability "intake": the part takes water from a source (ADR-001 D16, D17).
--   quality  "tainted" (lake, pond, river: default) or "clean"

local Check = require "LiveWater/LWT_Check"

local SPEC = { quality = Check.oneOf({ clean = true, tainted = true }, "tainted") }

local Intake = {}

function Intake.define(params)
    return Check.fields(params, SPEC)
end

return Intake
