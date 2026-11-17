-- LiveWater capability "valve": open or closed; closed, it cuts everything after it (D02).
--   open  state of a newly placed part (default true)

local Check = require "LiveWater/LWT_Check"

local SPEC = { open = Check.boolean(true) }

local Valve = {}

function Valve.define(params)
    return Check.fields(params, SPEC)
end

-- Closed when its state says so, else as placed.
function Valve.blocks(p, d)
    if d and d.open ~= nil then return not d.open end
    return not p.open
end

return Valve
