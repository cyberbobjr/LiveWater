-- LiveWater capability "conduit": water goes through the part between its connected sides
-- (pipe, and any part water flows through). No params.

local Check = require "LiveWater/LWT_Check"

local Conduit = {}

function Conduit.define(params)
    return Check.fields(params, {})
end

function Conduit.carries()
    return true
end

return Conduit
