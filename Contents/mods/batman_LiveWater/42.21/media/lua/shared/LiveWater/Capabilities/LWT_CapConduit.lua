-- LiveWater capability "conduit": water goes through the part between its connected sides
-- (pipe, and any part water flows through).
--   ports  optional (API revision 5): most pipes linked to the part, 1..4 (an inline part such
--          as a flow meter: 2); none = one per side

local Check = require "LiveWater/LWT_Check"

local SPEC = { ports = { valid = function(v) return Check.isInteger(v, 1, 4) end } }

local Conduit = {}

function Conduit.define(params)
    return Check.fields(params, SPEC)
end

function Conduit.carries()
    return true
end

function Conduit.ports(p)
    return p.ports
end

return Conduit
