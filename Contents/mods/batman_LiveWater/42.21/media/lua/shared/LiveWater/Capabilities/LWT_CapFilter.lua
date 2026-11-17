-- LiveWater capability "filter": makes water clean and wears by volume (ADR-001 D17, Q02).
--   capacity  litres one cartridge filters (default 500)

local Check = require "LiveWater/LWT_Check"

local SPEC = { capacity = Check.number(1, 1000000, 500) }

local Filter = {}

function Filter.define(params)
    return Check.fields(params, SPEC)
end

-- State: { used = litres filtered by the current cartridge }.
function Filter.purifies(p, d)
    return (d and d.used or 0) < p.capacity
end

function Filter.wear(p, d, litres)
    d.used = math.min(p.capacity, (d.used or 0) + litres)
end

return Filter
