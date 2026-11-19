if isClient() then return end
-- LiveWater: the reason an inlet's relays stay empty, noted on them for the fixture menu (ADR-001
-- D28, L09; ADR-009 D03). Chore of the clock, after the relays: one reason per inlet
-- (LWT_Diagnosis), written on its empty relays only (LWT_Relays:mark). The network outcome read is
-- the one of the last step (ten minutes old at most).
-- No game API here; dependencies are injected: { relays (LWT_Relays),
-- pumped = function(inlet part) -> a pump is on its network }.

local Diagnosis = require "LiveWater/LWT_Diagnosis"

local Diagnostics = {}
Diagnostics.__index = Diagnostics

function Diagnostics.new(deps)
    return setmetatable({ relays = deps.relays, pumped = deps.pumped }, Diagnostics)
end

function Diagnostics:reasonOf(part)
    local outlet = part.data and part.data.outlet
    return Diagnosis.inlet(outlet and outlet.state, self.pumped(part))
end

function Diagnostics:tick()
    local inlets = self.relays:inlets()
    for i = 1, #inlets do self.relays:mark(inlets[i], self:reasonOf(inlets[i])) end
end

return Diagnostics
