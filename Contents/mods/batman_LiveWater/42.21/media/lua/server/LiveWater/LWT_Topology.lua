if isClient() then return end
-- LiveWater: topology service on the authority (ADR-001 D06, D10). One place where parts join
-- or leave: the persistent registry (LWT_Registry) and the graph (LWT_Network) change
-- together, sprites follow (LWT_Sprites) and the public events are emitted:
--   partAdded (entry), partRemoved (entry), networkChanged (network id).
-- No game API here; dependencies are injected: { registry, network, catalog, events, sprites,
-- log = function(message) }.

local Grid = require "LiveWater/LWT_Grid"

local Topology = {}
Topology.__index = Topology

function Topology.new(deps)
    return setmetatable({
        registry = deps.registry, network = deps.network, catalog = deps.catalog,
        events = deps.events, sprites = deps.sprites, log = deps.log or print,
    }, Topology)
end

-- Build the graph from the active entries of the registry, in placement order (at load, no
-- event). An entry the graph refuses stays in the registry, inert, and is logged. Returns how
-- many parts joined the graph.
function Topology:rebuild()
    local entries, count = self.registry:active(), 0
    for i = 1, #entries do
        local e = entries[i]
        local ok, reason = self.network:add(e)
        if ok then
            count = count + 1
        else
            self.log("LiveWater: part " .. tostring(e.type) .. " at " .. Grid.key(e.x, e.y, e.z)
                .. " left out of the network: " .. tostring(reason))
        end
    end
    return count
end

function Topology:at(x, y, z)
    return self.registry:at(x, y, z)
end

-- Could a part of type `partType` join this square? Returns true, or false and
-- "unknown_part", "occupied", "ports_full". Changes nothing.
function Topology:canAdd(partType, x, y, z)
    if not self.catalog:has(partType) then return false, "unknown_part" end
    if self.registry:at(x, y, z) then return false, "occupied" end
    local ok, reason = self.network:canAdd({ type = partType, x = x, y = y, z = z })
    if not ok then return false, reason end
    return true
end

-- Add a part. Returns true and the registry entry, or false and a reason of canAdd.
function Topology:add(partType, x, y, z)
    local ok, reason = self:canAdd(partType, x, y, z)
    if not ok then return false, reason end
    local entry = self.registry:add(partType, x, y, z)
    local _, id = self.network:add(entry)
    self.sprites:around(x, y, z)
    self.events.emit("partAdded", entry)
    self.events.emit("networkChanged", id)
    return true, entry
end

-- Squares linked to the part of a square: list of { x, y, z }.
function Topology:linkedSquares(x, y, z)
    local part, out = self.network:part(x, y, z), {}
    if not part then return out end
    local links = self.network:linksOf(part)
    for i = 1, #links do
        for j = 1, #Grid.SIDES do
            local side = Grid.SIDES[j]
            if side.bit == links[i].bit then out[#out + 1] = { x + side.dx, y + side.dy, z } end
        end
    end
    return out
end

-- Remove the part of a square. Returns its entry, or nil when the square holds none. Every
-- network left by the split is announced once.
function Topology:remove(x, y, z)
    local entry = self.registry:remove(x, y, z)
    if not entry then return nil end
    local linked = self:linkedSquares(x, y, z)
    self.network:remove(x, y, z)
    self.sprites:around(x, y, z)
    self.events.emit("partRemoved", entry)
    local seen = {}
    for i = 1, #linked do
        local id = self.network:networkAt(linked[i][1], linked[i][2], linked[i][3])
        if id and not seen[id] then
            seen[id] = true
            self.events.emit("networkChanged", id)
        end
    end
    return entry
end

return Topology
