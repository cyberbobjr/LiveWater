if isClient() then return end
-- LiveWater: relay tanks of the house inlets, on the authority (ADR-001 D18, D21). Outlet handler
-- of the type "houseInlet" (LWT_Outlets) and chore of the clock (LWT_Clock):
--   tick()                 removes the relays left on squares that were not loaded, then keeps the
--                          relays of every inlet on a loaded square up to date (fixtures scanned
--                          again after REFRESH_HOURS of game time, or at once for a new inlet)
--   need(part)             litres missing in the inlet's relays that feed a plumbed fixture
--   deliver(part, litres)  fills those relays
--   release(part)          the inlet left: its relays are removed
--   mark(part, why)        the inlet's empty relays carry the reason (LWT_Diagnosis), the others none
-- A relay is an invisible 25 L tank one level above a fixture (LWT_RelayPlan), marked with the
-- ModData key LiveWaterRelay and its inlet; relays of Live Wire (LiveWireRelay) or of anything
-- else are never placed over, filled nor removed (D21).
-- No game API here; dependencies are injected: { store (persistent table: relays by inlet,
-- orphans), plumbing (port, LWT_GamePlumbing), world (isLoaded), now (function -> game hours),
-- setting (function(name) -> sandbox value), catalog, registry (active()), log, kind (outlet
-- type served, "houseInlet") }.

local Grid = require "LiveWater/LWT_Grid"
local InletArea = require "LiveWater/LWT_InletArea"
local RelayPlan = require "LiveWater/LWT_RelayPlan"

local Relays = {}
Relays.__index = Relays

Relays.CAPACITY = 25
Relays.REFRESH_HOURS = 1
Relays.EPSILON = 0.001
Relays.DEFAULT_RANGE = 20
Relays.DEFAULT_BASE_RANGE = 12

function Relays.new(deps)
    local store = deps.store
    store.relays = store.relays or {}
    store.orphans = store.orphans or {}
    return setmetatable({ store = store, plumbing = deps.plumbing, world = deps.world, now = deps.now,
        setting = deps.setting, catalog = deps.catalog, registry = deps.registry, log = deps.log or print,
        kind = deps.kind or "houseInlet", seen = {} }, Relays)
end

local function sortedKeys(t)
    local keys = {}
    for k in pairs(t) do keys[#keys + 1] = k end
    table.sort(keys)
    return keys
end

-- Value of a positive sandbox option, else `default`.
function Relays:option(name, default)
    local v = self.setting and self.setting(name)
    if type(v) == "number" and v > 0 then return v end
    return default
end

function Relays:ranges()
    return { building = self:option("InletRange", Relays.DEFAULT_RANGE),
        base = self:option("BaseRange", Relays.DEFAULT_BASE_RANGE) }
end

function Relays:isInlet(part)
    local _, _, outletType = self.catalog:first(part, "outlet")
    return outletType == self.kind
end

-- Relays recorded for an inlet key: { ["x,y,z"] = { x, y, z } }.
function Relays:own(key)
    local own = self.store.relays[key]
    if not own then
        own = {}
        self.store.relays[key] = own
    end
    return own
end

-- Remove one relay of the inlet `owner`; on a square not loaded it waits in the orphans.
function Relays:drop(owner, rkey, pos)
    self:own(owner)[rkey] = nil
    if not self.plumbing:removeRelay(pos.x, pos.y, pos.z, owner) then
        self.store.orphans[rkey] = { x = pos.x, y = pos.y, z = pos.z, owner = owner }
    end
end

-- Area of the inlet, or nil when it serves nothing.
function Relays:areaOf(part)
    return InletArea.of(self.plumbing, part.x, part.y, part.z, self:ranges())
end

-- Place the relays the inlet wants, remove the ones it no longer wants. `force` scans at once.
function Relays:refresh(part, force)
    local key, now = Grid.key(part.x, part.y, part.z), self.now()
    local seen = self.seen[key]
    if not force and seen and now >= seen and now - seen < Relays.REFRESH_HOURS then return end
    self.seen[key] = now
    local area = self:areaOf(part)
    local wanted = RelayPlan.wanted(area and self.plumbing:fixtures(area) or {}, key)
    local own = self:own(key)
    local keys = sortedKeys(wanted)
    for i = 1, #keys do
        local pos = wanted[keys[i]]
        local relay = self.plumbing:relay(pos.x, pos.y, pos.z)
        if not relay then
            self.plumbing:placeRelay(pos.x, pos.y, pos.z, key, Relays.CAPACITY)
            own[keys[i]] = pos
        elseif relay.owner == key then
            own[keys[i]] = pos
        end
    end
    keys = sortedKeys(own)
    for i = 1, #keys do
        if not wanted[keys[i]] then self:drop(key, keys[i], own[keys[i]]) end
    end
end

-- Relays of the inlet that feed a plumbed fixture and have room: list of { x, y, z, free }.
function Relays:feeding(part)
    local key, out = Grid.key(part.x, part.y, part.z), {}
    local own = self:own(key)
    local keys = sortedKeys(own)
    for i = 1, #keys do
        local pos = own[keys[i]]
        local relay = self.plumbing:relay(pos.x, pos.y, pos.z)
        if relay and relay.owner == key and relay.feeds and relay.free > Relays.EPSILON then
            out[#out + 1] = { x = pos.x, y = pos.y, z = pos.z, free = relay.free }
        end
    end
    return out
end

function Relays:need(part)
    self:refresh(part)
    local list, total = self:feeding(part), 0
    for i = 1, #list do total = total + list[i].free end
    return total
end

function Relays:deliver(part, litres, quality)
    local list, left = self:feeding(part), litres
    for i = 1, #list do
        if left <= Relays.EPSILON then break end
        local r = list[i]
        left = left - self.plumbing:fillRelay(r.x, r.y, r.z, math.min(left, r.free), quality)
    end
end

function Relays:release(part)
    local key = Grid.key(part.x, part.y, part.z)
    local own = self:own(key)
    local keys = sortedKeys(own)
    for i = 1, #keys do self:drop(key, keys[i], own[keys[i]]) end
    self.store.relays[key] = nil
    self.seen[key] = nil
end

function Relays:mark(part, why)
    local key = Grid.key(part.x, part.y, part.z)
    local own = self:own(key)
    local keys = sortedKeys(own)
    for i = 1, #keys do
        local pos = own[keys[i]]
        local relay = self.plumbing:relay(pos.x, pos.y, pos.z)
        if relay and relay.owner == key then
            self.plumbing:markRelay(pos.x, pos.y, pos.z, relay.amount <= Relays.EPSILON and why or nil)
        end
    end
end

-- Inlets of the registry on a loaded square.
function Relays:inlets()
    local out, entries = {}, self.registry:active()
    for i = 1, #entries do
        local e = entries[i]
        if self:isInlet(e) and self.world:isLoaded(e.x, e.y, e.z) then out[#out + 1] = e end
    end
    return out
end

function Relays:tick()
    local orphans = self.store.orphans
    local keys = sortedKeys(orphans)
    for i = 1, #keys do
        local o = orphans[keys[i]]
        if self.plumbing:removeRelay(o.x, o.y, o.z, o.owner) then orphans[keys[i]] = nil end
    end
    local inlets = self:inlets()
    for i = 1, #inlets do self:refresh(inlets[i]) end
end

return Relays
