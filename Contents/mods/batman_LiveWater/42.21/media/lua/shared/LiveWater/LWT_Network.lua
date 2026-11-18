-- LiveWater: network graph (ADR-001 D10, D12-D15). Pure, no game API: the catalog of part
-- types (LWT_Parts) is injected; this module never names a capability kind, it asks hooks.
-- One part per square. Two orthogonal neighbours on the same level are linked when each
-- offers the side facing the other. Linked parts form a network (merge on add, split on
-- remove). Parts are kept by reference: the owner's state changes (valve) are seen here.
-- Water starts at the parts that pressurize, goes through parts that carry and do not
-- block; a reached part that does not carry (outlet) or blocks (closed valve) ends a path.

local Grid = require "LiveWater/LWT_Grid"

local Network = {}
Network.__index = Network

function Network.new(catalog)
    return setmetatable({ catalog = catalog, parts = {}, netOf = {}, sets = {}, lastNet = 0, seq = 0 },
        Network)
end

local function keyOf(part)
    return Grid.key(part.x, part.y, part.z)
end

-- Links of `part` (stored or not) to the stored parts around it: list of { bit, key }.
function Network:linksOf(part)
    local links, sides = {}, self.catalog:sides(part.type)
    for i = 1, #Grid.SIDES do
        local side = Grid.SIDES[i]
        if Grid.has(sides, side.bit) then
            local key = Grid.key(part.x + side.dx, part.y + side.dy, part.z)
            local other = self.parts[key]
            if other and Grid.has(self.catalog:sides(other.type), side.opposite) then
                links[#links + 1] = { bit = side.bit, key = key }
            end
        end
    end
    return links
end

-- Most links the part accepts: its ports, else one per side.
function Network:limitOf(part)
    return self.catalog:first(part, "ports") or #Grid.SIDES
end

-- Would the new part and each linked neighbour stay within their ports (D14)?
function Network:fits(part, links)
    if #links > self:limitOf(part) then return false end
    for i = 1, #links do
        local other = self.parts[links[i].key]
        if #self:linksOf(other) + 1 > self:limitOf(other) then return false end
    end
    return true
end

-- Flood the parts linked to `start` into network `id`.
function Network:label(start, id)
    local set = self.sets[id] or {}
    self.sets[id] = set
    local queue, head = { start }, 1
    self.netOf[start], set[start] = id, true
    while head <= #queue do
        local links = self:linksOf(self.parts[queue[head]])
        head = head + 1
        for i = 1, #links do
            local key = links[i].key
            local old = self.netOf[key]
            if old ~= id then
                if old then self.sets[old][key] = nil end
                self.netOf[key], set[key] = id, true
                queue[#queue + 1] = key
            end
        end
    end
end

function Network:newId()
    self.lastNet = self.lastNet + 1
    return self.lastNet
end

local function isEmpty(set)
    for _ in pairs(set) do return false end
    return true
end

-- Could the part { type, x, y, z } be added? Returns true and its links, or false and
-- "unknown_part", "occupied", "ports_full". Changes nothing.
function Network:canAdd(part)
    if not self.catalog:has(part.type) then return false, "unknown_part" end
    if self.parts[keyOf(part)] then return false, "occupied" end
    local links = self:linksOf(part)
    if not self:fits(part, links) then return false, "ports_full" end
    return true, links
end

-- Add a placed part { type, x, y, z, order?, data? }. `order` (placement order) is given
-- when the part is reloaded, else assigned. Returns true and the network id, or false and
-- "unknown_part", "occupied", "ports_full".
function Network:add(part)
    local ok, links = self:canAdd(part)
    if not ok then return false, links end
    local key = keyOf(part)
    if part.order == nil then part.order = self.seq + 1 end
    if part.order > self.seq then self.seq = part.order end
    self.parts[key] = part
    local target, touched = nil, {}
    for i = 1, #links do
        local id = self.netOf[links[i].key]
        touched[id] = true
        if target == nil or id < target then target = id end
    end
    self:label(key, target or self:newId())
    for id in pairs(touched) do
        if isEmpty(self.sets[id]) then self.sets[id] = nil end
    end
    return true, self.netOf[key]
end

-- Remove the part of a square. Returns it, or nil when the square is empty. The rest of its
-- network splits when the part held it together; the first neighbour keeps the network id.
function Network:remove(x, y, z)
    local key = Grid.key(x, y, z)
    local part = self.parts[key]
    if not part then return nil end
    local links = self:linksOf(part)
    local old = self.netOf[key]
    for member in pairs(self.sets[old]) do self.netOf[member] = nil end
    self.sets[old] = nil
    self.parts[key] = nil
    for i = 1, #links do
        if not self.netOf[links[i].key] then
            self:label(links[i].key, i == 1 and old or self:newId())
        end
    end
    return part
end

function Network:part(x, y, z)
    return self.parts[Grid.key(x, y, z)]
end

function Network:networkAt(x, y, z)
    return self.netOf[Grid.key(x, y, z)]
end

-- Ids of the networks, sorted.
function Network:ids()
    local list = {}
    for id in pairs(self.sets) do list[#list + 1] = id end
    table.sort(list)
    return list
end

local function byOrder(a, b)
    return a.order < b.order
end

-- Parts of a network, in placement order.
function Network:members(id)
    local list = {}
    for key in pairs(self.sets[id] or {}) do list[#list + 1] = self.parts[key] end
    table.sort(list, byOrder)
    return list
end

-- Side mask of the links of the part on a square (0 when alone or absent).
function Network:mask(x, y, z)
    local part = self:part(x, y, z)
    if not part then return 0 end
    local mask, links = 0, self:linksOf(part)
    for i = 1, #links do mask = mask + links[i].bit end
    return mask
end

-- Sprite the part on a square shows for its links (ADR-001 D12).
function Network:sprite(x, y, z)
    local part = self:part(x, y, z)
    return part and self.catalog:sprite(part.type, self:mask(x, y, z)) or nil
end

-- Where water gets in a network: pipe distance from the nearest part that pressurizes.
-- Returns the reached parts as a list in service order (distance, then placement order) and
-- the same nodes by key; node = { key, part, dist, from = key of the previous node, root = true
-- for a part that pressurizes }.
function Network:reach(id)
    local catalog, byKey, queue, head = self.catalog, {}, {}, 1
    local members = self:members(id)
    for i = 1, #members do
        local part = members[i]
        if catalog:any(part, "pressurizes") then
            local node = { key = keyOf(part), part = part, dist = 0, root = true }
            byKey[node.key] = node
            queue[#queue + 1] = node
        end
    end
    while head <= #queue do
        local node = queue[head]
        head = head + 1
        local part = node.part
        if not catalog:closed(part) and (node.root or catalog:any(part, "carries")) then
            local links = self:linksOf(part)
            for i = 1, #links do
                local key = links[i].key
                if not byKey[key] then
                    local child = { key = key, part = self.parts[key], dist = node.dist + 1, from = node.key }
                    byKey[key] = child
                    queue[#queue + 1] = child
                end
            end
        end
    end
    table.sort(queue, function(a, b)
        if a.dist ~= b.dist then return a.dist < b.dist end
        return a.part.order < b.part.order
    end)
    return queue, byKey
end

-- The parts a closed part keeps from the water: not reached (`byKey` from reach), but found from
-- a reached closed part through parts that carry (closed or not). Returns a list of { key, part }.
function Network:behindClosed(byKey)
    local catalog, seen, queue, head, out = self.catalog, {}, {}, 1, {}
    for key, node in pairs(byKey) do
        if catalog:closed(node.part) then
            seen[key] = true
            queue[#queue + 1] = node.part
        end
    end
    while head <= #queue do
        local part = queue[head]
        head = head + 1
        local links = self:linksOf(part)
        for i = 1, #links do
            local key = links[i].key
            if not seen[key] and not byKey[key] then
                seen[key] = true
                local other = self.parts[key]
                out[#out + 1] = { key = key, part = other }
                if catalog:any(other, "carries") then queue[#queue + 1] = other end
            end
        end
    end
    return out
end

return Network
