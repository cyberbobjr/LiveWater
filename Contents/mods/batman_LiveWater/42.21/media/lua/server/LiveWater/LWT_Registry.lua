if isClient() then return end
-- LiveWater: persistent registry of placed parts (ADR-001 D03, D04, D10). The store is the
-- global ModData table, injected by the adapter (a plain table in tests); this module calls
-- no game API. Layout:
--   store.seq                 last placement order given (orders are never reused)
--   store.parts["x,y,z"]      entry = { v, type, x, y, z, order, data = { [kind] = state }, facing?,
--                             cuts?, apart? } (facing of the sprite set down, ADR-008 D08; sides a
--                             wall cuts or kept apart, ADR-002, ADR-006: recorded by the topology)
-- Entries are kept as they are: fields this version does not know (newer schema, absent
-- capability) stay untouched. A part whose type is not registered (mod removed) stays in the
-- store, inert, and is active again when its type is registered again.
-- The catalog only needs has(id) (LWT_Parts).

local Grid = require "LiveWater/LWT_Grid"

local Registry = {}
Registry.__index = Registry

Registry.SCHEMA = 1

function Registry.new(store, catalog)
    store.parts = store.parts or {}
    store.seq = store.seq or 0
    return setmetatable({ store = store, catalog = catalog }, Registry)
end

-- New entry for a part of a registered type on a free square. Returns it, or nil and
-- "unknown_part" or "occupied".
function Registry:add(partType, x, y, z)
    if not self.catalog:has(partType) then return nil, "unknown_part" end
    local key = Grid.key(x, y, z)
    if self.store.parts[key] then return nil, "occupied" end
    self.store.seq = self.store.seq + 1
    local entry = { v = Registry.SCHEMA, type = partType, x = x, y = y, z = z, order = self.store.seq, data = {} }
    self.store.parts[key] = entry
    return entry
end

-- Remove and return the entry of a square, or nil.
function Registry:remove(x, y, z)
    local key = Grid.key(x, y, z)
    local entry = self.store.parts[key]
    self.store.parts[key] = nil
    return entry
end

function Registry:at(x, y, z)
    return self.store.parts[Grid.key(x, y, z)]
end

function Registry:isActive(entry)
    return self.catalog:has(entry.type)
end

-- Entries whose type is registered, in placement order.
function Registry:active()
    local list = {}
    for _, entry in pairs(self.store.parts) do
        if self:isActive(entry) then list[#list + 1] = entry end
    end
    table.sort(list, function(a, b) return a.order < b.order end)
    return list
end

return Registry
