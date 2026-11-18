if isClient() then return end
-- LiveWater: fix of the plumbed washing machines in multiplayer, for the washers LiveWater feeds
-- (ADR-001 L13, Q08). Two defects of 42.22, confirmed statically:
--   1. ClothingWasherLogic.update stops a washer that ran dry on the server (setActivated(false))
--      without sending WASHER_STATE; the clients skip that check and keep it "running" (sound,
--      clothes locked inside, no switch since it shows no water). Fix: when a washer fed by one of
--      our relays is off on the server, its state is sent once (sendObjectChange WASHER_STATE).
--   2. IsoClothingWasher.saveChange / loadChange hand every change to its logic, which writes only
--      WASHER_STATE: the plumbed state (USES_EXTERNAL_WATER_SOURCE) never reaches the clients.
--      Fix: a plain washer fed by one of our relays gets the ModData mark LiveWaterWasher, sent with
--      transmitModData; the client applies it (LWT_WasherClient).
-- Chore of the clock, on a server only (solo has one copy of each object), while the sandbox
-- option WasherFix is on. No game API here; dependencies are injected: { relays (inlets(),
-- positions(part)), plumbing (washers(x, y, z) of a relay: { x, y, z, activated, plain, marked },
-- sendWasherState, markWasher), enabled = function -> bool, multiplayer = function -> bool }.

local Grid = require "LiveWater/LWT_Grid"

local WasherFix = {}
WasherFix.__index = WasherFix


function WasherFix.new(deps)
    return setmetatable({ relays = deps.relays, plumbing = deps.plumbing, enabled = deps.enabled,
        multiplayer = deps.multiplayer, told = {} }, WasherFix)
end

function WasherFix:fix(w)
    local key = Grid.key(w.x, w.y, w.z)
    if w.plain and not w.marked then self.plumbing:markWasher(w.x, w.y, w.z) end
    if w.activated then
        self.told[key] = true
    elseif self.told[key] ~= false then
        self.plumbing:sendWasherState(w.x, w.y, w.z)
        self.told[key] = false
    end
end

function WasherFix:tick()
    if not (self.multiplayer() and self.enabled()) then return end
    local inlets = self.relays:inlets()
    for i = 1, #inlets do
        local positions = self.relays:positions(inlets[i])
        for j = 1, #positions do
            local p = positions[j]
            local washers = self.plumbing:washers(p.x, p.y, p.z)
            for k = 1, #washers do self:fix(washers[k]) end
        end
    end
end

return WasherFix
