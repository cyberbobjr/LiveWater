-- LiveWater capability "controller": decides when a valve opens (ADR-001 D02, D19).
--   mode  "manual" (default) or "timer"; the timer behaviour arrives with step E12.

local Check = require "LiveWater/LWT_Check"

local SPEC = { mode = Check.oneOf({ manual = true, timer = true }, "manual") }

local Controller = {}

function Controller.define(params)
    return Check.fields(params, SPEC)
end

return Controller
