if isClient() then return end
-- LiveWater: barrels connected to a house inlet, on the authority (ADR-001 D27, D28, L01-L03, L06,
-- L07, L12). A barrel or rain collector inside the building of an inlet, or on its roof, is
-- connected with a pipe wrench: no pipe, no pump. Chore of the clock after the relays
-- (LWT_Relays): every ten minutes the barrels of each inlet on a loaded square fill its relay tanks
-- (shared reserve, gravity: LWT_Reserve); the network tops up what is still missing after.
--   connect(x, y, z)       -> true, or false and "not_barrel", "no_inlet"
--   disconnect(x, y, z)    -> true, or false and "not_connected"
--   toggleReserve(x, y, z) -> true, or false and "not_connected"
--   forget(part)           an inlet left: its barrels are disconnected
--   placed(x, y, z)        an object was set down there: a barrel carrying the mark of a connection
--                          it no longer has (picked up elsewhere) forgets it (L12)
--   has(part)              the inlet has connected barrels
--   shortOf(part)          why the inlet's relays stayed short after the last chore, or nil
--   tick()
-- The connection lives in the persistent store (barrels by inlet key) and is mirrored on the
-- barrel (ModData LiveWaterBarrel = { inlet, reserve }) for the client menus. A barrel gone from a
-- loaded square is dropped. No game API here; dependencies are injected: { store, plumbing (port,
-- LWT_GamePlumbing), world (hasPower), relays (LWT_Relays: inlets, areaOf, feeding), lifted =
-- function(inlet part) -> a pump in its network }.

local Grid = require "LiveWater/LWT_Grid"
local Reserve = require "LiveWater/LWT_Reserve"

local HouseBarrels = {}
HouseBarrels.__index = HouseBarrels

-- Version of the persisted barrel records and of the mark on the barrel (D04).
HouseBarrels.SCHEMA = 1

function HouseBarrels.new(deps)
    local store = deps.store
    store.barrels = store.barrels or {}
    return setmetatable({ store = store, plumbing = deps.plumbing, world = deps.world, relays = deps.relays,
        lifted = deps.lifted, short = {} }, HouseBarrels)
end

local function sortedKeys(t)
    local keys = {}
    for k in pairs(t) do keys[#keys + 1] = k end
    table.sort(keys)
    return keys
end

local function keyOf(part)
    return Grid.key(part.x, part.y, part.z)
end

-- Inlet key and record of the barrel on (x, y, z), or nil.
function HouseBarrels:recordAt(x, y, z)
    local bkey = Grid.key(x, y, z)
    for inlet, list in pairs(self.store.barrels) do
        if list[bkey] then return inlet, list[bkey] end
    end
    return nil
end

-- The closest inlet on a loaded square whose area reaches (x, y, z), or nil.
function HouseBarrels:inletFor(x, y, z)
    local best, distance
    local inlets = self.relays:inlets()
    for i = 1, #inlets do
        local p = inlets[i]
        local area = self.relays:areaOf(p)
        if area and area:reaches(x, y, z) then
            local d = (p.x - x) * (p.x - x) + (p.y - y) * (p.y - y)
            if not best or d < distance then best, distance = p, d end
        end
    end
    return best
end

function HouseBarrels:write(inlet, x, y, z, record)
    self.plumbing:markBarrel(x, y, z,
        record and { v = HouseBarrels.SCHEMA, inlet = inlet, reserve = record.reserve } or nil)
end

function HouseBarrels:connect(x, y, z)
    if not self.plumbing:barrel(x, y, z) then return false, "not_barrel" end
    local inlet = self:inletFor(x, y, z)
    if not inlet then return false, "no_inlet" end
    if self:recordAt(x, y, z) then self:disconnect(x, y, z) end
    local ikey = keyOf(inlet)
    local list = self.store.barrels[ikey] or {}
    self.store.barrels[ikey] = list
    local record = { v = HouseBarrels.SCHEMA, x = x, y = y, z = z, reserve = false }
    list[Grid.key(x, y, z)] = record
    self:write(ikey, x, y, z, record)
    return true
end

function HouseBarrels:disconnect(x, y, z)
    local inlet = self:recordAt(x, y, z)
    if not inlet then return false, "not_connected" end
    self.store.barrels[inlet][Grid.key(x, y, z)] = nil
    self:write(inlet, x, y, z, nil)
    return true
end

function HouseBarrels:toggleReserve(x, y, z)
    local inlet, record = self:recordAt(x, y, z)
    if not inlet then return false, "not_connected" end
    record.reserve = not record.reserve
    self:write(inlet, x, y, z, record)
    return true
end

function HouseBarrels:forget(part)
    local ikey = keyOf(part)
    local list = self.store.barrels[ikey]
    if not list then return end
    local keys = sortedKeys(list)
    for i = 1, #keys do
        local r = list[keys[i]]
        self:write(ikey, r.x, r.y, r.z, nil)
    end
    self.store.barrels[ikey] = nil
    self.short[ikey] = nil
end

-- Sources of the reserve of an inlet (LWT_Reserve); drops the barrels gone from loaded squares.
function HouseBarrels:sources(inlet, list)
    local out, keys, lifted = {}, sortedKeys(list), self.lifted and self.lifted(inlet)
    for i = 1, #keys do
        local r = list[keys[i]]
        local info, loaded = self.plumbing:barrel(r.x, r.y, r.z)
        if info then
            out[#out + 1] = { key = keys[i], x = r.x, y = r.y, z = r.z, amount = info.amount, usable = info.waterOnly,
                reserve = r.reserve, lifted = lifted or self.world:hasPower(r.x, r.y, r.z) }
        elseif loaded then
            list[keys[i]] = nil
        end
    end
    return out
end

-- The barrels of one inlet fill its relays. Returns the reason its relays stay short, or nil.
function HouseBarrels:supply(inlet, list)
    local sources = self:sources(inlet, list)
    local needs = self.relays:feeding(inlet)
    for i = 1, #needs do needs[i].key = Grid.key(needs[i].x, needs[i].y, needs[i].z) end
    local moves, reasons = Reserve.plan(sources, needs)
    local byKey = {}
    for i = 1, #sources do byKey[sources[i].key] = sources[i] end
    for i = 1, #needs do byKey[needs[i].key] = needs[i] end
    for i = 1, #moves do
        local s, n = byKey[moves[i].source], byKey[moves[i].need]
        self.plumbing:transfer(s.x, s.y, s.z, n.x, n.y, n.z, moves[i].litres)
    end
    for i = 1, #needs do
        if reasons[i] then return reasons[i] end
    end
    return nil
end

function HouseBarrels:placed(x, y, z)
    if self:recordAt(x, y, z) then return end
    local info = self.plumbing:barrel(x, y, z)
    if info and info.mark then self.plumbing:markBarrel(x, y, z, nil) end
end

function HouseBarrels:has(part)
    local list = self.store.barrels[keyOf(part)]
    if not list then return false end
    for _ in pairs(list) do return true end
    return false
end

function HouseBarrels:shortOf(part)
    return self.short[keyOf(part)]
end

function HouseBarrels:tick()
    local inlets = self.relays:inlets()
    for i = 1, #inlets do
        local ikey = keyOf(inlets[i])
        local list = self.store.barrels[ikey]
        self.short[ikey] = list and self:supply(inlets[i], list) or nil
    end
end

return HouseBarrels
