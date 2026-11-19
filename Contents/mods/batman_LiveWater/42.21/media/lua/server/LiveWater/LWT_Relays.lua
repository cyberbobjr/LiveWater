if isClient() then return end
-- LiveWater: relay tanks of the house inlets, on the authority (ADR-001 D18, D21). Outlet handler
-- of the type "houseInlet" (LWT_Outlets) and chore of the clock (LWT_Clock):
--   tick()                 removes the relays left on squares that were not loaded, then keeps the
--                          relays of every inlet on a loaded square up to date
--   touched(x, y)          a fixture or a water tank was set down or taken on that square
--   chunkLoaded(x, y, size) the squares x..x+size-1, y..y+size-1 were loaded
-- Survey on events only (D10): the fixtures of an inlet are scanned again at the next step only
-- when it is new or loaded again, when something touched or loaded near it (within the larger of
-- its two ranges), or when the city water stopped or came back; never on a timer.
--   need(part)             litres missing in the inlet's relays that feed a plumbed fixture; 0
--                          while the inlet's square is not loaded (the relays wait for the
--                          player's return, ADR-006 D06)
--   deliver(part, litres)  fills those relays
--   release(part)          the inlet left: its relays are removed
--   mark(part, why)        the inlet's empty relays carry the reason (LWT_Diagnosis), the others none
--   positions(part)        squares of the inlet's relays, sorted: list of { x, y, z }
--   fixtureStates(part)    fixtures of the inlet's area and how they get water (network view,
--                          ADR-008 D06): list of { x, y, z, status }, status "fed" (plumbed, fed by
--                          one of LiveWater's relays that holds water), "dry" (plumbed, LiveWater's
--                          relay empty or not placed yet), "notPlumbed", "other" (another tank: a
--                          Live Wire relay, a barrel)
-- A relay is an invisible 25 L tank one level above a fixture (LWT_RelayPlan), marked with the
-- ModData key LiveWaterRelay and its inlet; relays of Live Wire (LiveWireRelay) or of anything
-- else are never placed over, filled nor removed (D21).
-- No game API here; dependencies are injected: { store (persistent table: relays by inlet,
-- orphans), plumbing (port, LWT_GamePlumbing), world (isLoaded),
-- setting (function(name) -> sandbox value), catalog, registry (active()), log, kind (outlet
-- type served, "houseInlet") }.

local Grid = require "LiveWater/LWT_Grid"
local InletArea = require "LiveWater/LWT_InletArea"
local RelayPlan = require "LiveWater/LWT_RelayPlan"
local WaterObjects = require "LiveWater/LWT_WaterObjects"

local Relays = {}
Relays.__index = Relays

Relays.CAPACITY = WaterObjects.RELAY_LITRES
-- Version of the persisted relay and orphan records (D04).
Relays.SCHEMA = 1
Relays.EPSILON = 0.001
Relays.DEFAULT_RANGE = 20
Relays.DEFAULT_BASE_RANGE = 12

function Relays.new(deps)
    local store = deps.store
    store.relays = store.relays or {}
    store.orphans = store.orphans or {}
    return setmetatable({ store = store, plumbing = deps.plumbing, world = deps.world,
        setting = deps.setting, catalog = deps.catalog, registry = deps.registry, log = deps.log or print,
        kind = deps.kind or "houseInlet", seen = {}, dirty = {}, loaded = {}, known = {} }, Relays)
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

-- Relays recorded for an inlet key: { ["x,y,z"] = { v, x, y, z } }.
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
        self.store.orphans[rkey] = { v = Relays.SCHEMA, x = pos.x, y = pos.y, z = pos.z, owner = owner }
    end
end

-- Area of the inlet, or nil when it serves nothing.
function Relays:areaOf(part)
    return InletArea.of(self.plumbing, part.x, part.y, part.z, self:ranges())
end

-- Record a relay of the inlet; a record already there is kept with its unknown fields (D04).
local function keep(own, rkey, pos)
    local record = own[rkey]
    if record then
        record.v = record.v or Relays.SCHEMA
        return
    end
    own[rkey] = { v = Relays.SCHEMA, x = pos.x, y = pos.y, z = pos.z }
end

-- Place the relays the inlet wants, remove the ones it no longer wants. Scans the fixtures when
-- the inlet was never surveyed, was touched since, or `force`.
function Relays:refresh(part, force)
    local key = Grid.key(part.x, part.y, part.z)
    if not force and self.seen[key] and not self.dirty[key] then return end
    self.seen[key] = true
    self.dirty[key] = nil
    local area, served = self:areaOf(part), {}
    local found = area and self.plumbing:fixtures(area) or {}
    for i = 1, #found do
        if area:serves(found[i], key) then served[#served + 1] = found[i] end
    end
    local wanted = RelayPlan.wanted(served, key)
    local own = self:own(key)
    local keys = sortedKeys(wanted)
    for i = 1, #keys do
        local pos = wanted[keys[i]]
        local relay = self.plumbing:relay(pos.x, pos.y, pos.z)
        if not relay then
            self.plumbing:placeRelay(pos.x, pos.y, pos.z, key, Relays.CAPACITY)
            keep(own, keys[i], pos)
        elseif relay.owner == key then
            keep(own, keys[i], pos)
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
    if not self.world:isLoaded(part.x, part.y, part.z) then return 0 end
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
    self.dirty[key] = nil
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

function Relays:positions(part)
    local own, out = self:own(Grid.key(part.x, part.y, part.z)), {}
    local keys = sortedKeys(own)
    for i = 1, #keys do out[i] = own[keys[i]] end
    return out
end

-- How a fixture of the area { plumbed, source } gets water.
function Relays:fixtureStatus(f)
    if not f.plumbed then return "notPlumbed" end
    local src = f.source
    if src == "other" then return "other" end
    local relay = type(src) == "table" and self.plumbing:relay(src.x, src.y, src.z)
    if relay and relay.amount > Relays.EPSILON then return "fed" end
    return "dry"
end

function Relays:fixtureStates(part)
    local key, out = Grid.key(part.x, part.y, part.z), {}
    local area = self:areaOf(part)
    local found = area and self.plumbing:fixtures(area) or {}
    for i = 1, #found do
        local f = found[i]
        if area:serves(f, key) then
            out[#out + 1] = { x = f.x, y = f.y, z = f.z, status = self:fixtureStatus(f) }
        end
    end
    return out
end

-- Inlets of the registry, then those on a loaded square.
function Relays:allInlets()
    local all, loaded, entries = {}, {}, self.registry:active()
    for i = 1, #entries do
        local e = entries[i]
        if self:isInlet(e) then
            all[#all + 1] = e
            if self.world:isLoaded(e.x, e.y, e.z) then loaded[#loaded + 1] = e end
        end
    end
    return all, loaded
end

function Relays:inlets()
    local _, loaded = self:allInlets()
    return loaded
end

-- Squares around an inlet where an event may change what it serves (the larger range).
function Relays:reach()
    local r = self:ranges()
    return math.max(r.building, r.base)
end

-- Inlets known at the last step whose reach meets the rectangle x1..x2, y1..y2: marked dirty.
function Relays:touchRect(x1, y1, x2, y2)
    local reach, known = self:reach(), self.known
    for i = 1, #known do
        local p = known[i]
        if p.x + reach >= x1 and p.x - reach <= x2 and p.y + reach >= y1 and p.y - reach <= y2 then
            self.dirty[Grid.key(p.x, p.y, p.z)] = true
        end
    end
end

function Relays:touched(x, y)
    self:touchRect(x, y, x, y)
end

function Relays:chunkLoaded(x, y, size)
    self:touchRect(x, y, x + size - 1, y + size - 1)
end

function Relays:tick()
    local orphans = self.store.orphans
    local keys = sortedKeys(orphans)
    for i = 1, #keys do
        local o = orphans[keys[i]]
        if self.plumbing:removeRelay(o.x, o.y, o.z, o.owner) then orphans[keys[i]] = nil end
    end
    local all, inlets = self:allInlets()
    if #inlets > 0 then
        -- the shut-off makes the original fixtures of the buildings eligible (LWT_GamePlumbing)
        local runs = self.plumbing:cityWaterRuns()
        if self.cityRuns ~= nil and runs ~= self.cityRuns then self.seen = {} end
        self.cityRuns = runs
    end
    local loaded = {}
    for i = 1, #inlets do
        local key = Grid.key(inlets[i].x, inlets[i].y, inlets[i].z)
        if not self.loaded[key] then self.seen[key] = nil end
        loaded[key] = true
        self:refresh(inlets[i])
    end
    self.known, self.loaded = all, loaded
end

return Relays
