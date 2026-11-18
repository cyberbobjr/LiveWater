if isClient() then return end
-- LiveWater: clean removal of LiveWater from a world (ADR-001 P21, L14), on the authority, so that the
-- save stays readable once the mod is unsubscribed. Started by an admin (command removeLiveWater):
--   start()   every part of a registered type on a loaded square leaves the topology and its tile is
--             removed; partRemoved takes its relay tanks and barrel connections with it (LWT_Relays,
--             LWT_HouseBarrels: relays on squares not loaded wait in their orphans until loaded);
--             the fixtures keep their vanilla state (plumbed, now without an outside source).
--             Returns how many parts went and how many wait on squares not loaded.
--   tick()    chore of the clock: once started, the parts whose square is now loaded go too; nil
--             when not started.
--   done()    nothing of a registered type is left.
--   started() the removal was started: the topology refuses every new part from then on (a part
--             set down stays a decoration the player can pick up again, never taken away).
-- Parts of a type no longer registered stay in the registry untouched (D03). The flag lives in the
-- persistent store (store.removal), so the removal goes on after a restart. No game API here;
-- dependencies are injected: { store, registry (active()), topology (remove), world (isLoaded,
-- removePart), log }.

local Removal = {}
Removal.__index = Removal

Removal.SCHEMA = 1

function Removal.new(deps)
    return setmetatable({ store = deps.store, registry = deps.registry, topology = deps.topology, world = deps.world,
        log = deps.log or print }, Removal)
end

function Removal:start()
    self.store.removal = self.store.removal or { v = Removal.SCHEMA }
    local removed, waiting = self:tick()
    self.log("LiveWater: removal started, " .. removed .. " part(s) removed, " .. waiting
        .. " waiting for their square to load")
    return removed, waiting
end

function Removal:tick()
    if not self.store.removal then return nil end
    local parts, removed, waiting = self.registry:active(), 0, 0
    for i = 1, #parts do
        local e = parts[i]
        if self.world:isLoaded(e.x, e.y, e.z) then
            self.topology:remove(e.x, e.y, e.z)
            self.world:removePart(e.x, e.y, e.z, e.type)
            removed = removed + 1
        else
            waiting = waiting + 1
        end
    end
    return removed, waiting
end

function Removal:started()
    return self.store.removal ~= nil
end

function Removal:done()
    return #self.registry:active() == 0
end

return Removal
