if isClient() then return end
-- LiveWater: topology service on the authority (ADR-001 D06, D10). One place where parts join
-- or leave: the persistent registry (LWT_Registry) and the graph (LWT_Network) change
-- together, sprites follow (LWT_Sprites) and the public events are emitted:
--   partAdded (entry), partRemoved (entry), networkChanged (network id).
-- No game API here; dependencies are injected: { registry, network, catalog, events, sprites,
-- sites (port: site(x, y, z) -> the place a part asks, see LWT_GameSite), log = function(message),
-- closed (optional function -> true once LiveWater was removed from the world: no part joins any
-- more, E21), edges (optional port: edge(x, y, z, north) -> "wall", "fence" or nil, ADR-002) }.
-- A part records `cuts`, the sides a solid wall cuts, when it joins and when an edge object
-- changes around it (relink); the graph reads only that record (squares far away are not loaded).
-- A part records `facing`, the facing of the sprite it was set down with (ADR-008 D08): the graph
-- asks the catalog the sides of that facing (an inline part on its axis), kept in the registry.
-- A part joins only where its capabilities accept the place (Parts:attach, e.g. an intake next
-- to a water source); what they find is recorded in the part's state.

local Grid = require "LiveWater/LWT_Grid"

local Topology = {}
Topology.__index = Topology

function Topology.new(deps)
    return setmetatable({
        registry = deps.registry, network = deps.network, catalog = deps.catalog,
        events = deps.events, sprites = deps.sprites, sites = deps.sites, log = deps.log or print,
        closed = deps.closed, edges = deps.edges,
    }, Topology)
end

-- Mask of the sides of square (x, y, z) a solid wall cuts (0 without an edges port).
function Topology:cutsAt(x, y, z)
    if not self.edges then return 0 end
    local out = 0
    for i = 1, #Grid.SIDES do
        local side = Grid.SIDES[i]
        local ex, ey, north = Grid.edgeOf(x, y, side.bit)
        if self.edges:edge(ex, ey, z, north) == "wall" then out = out + side.bit end
    end
    return out
end

-- Record the cuts of the entry on a square, nil when none (registry entry and graph node alike).
function Topology:recordCuts(entry)
    local cuts = self:cutsAt(entry.x, entry.y, entry.z)
    entry.cuts = cuts > 0 and cuts or nil
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

function Topology:siteAt(x, y, z)
    return self.sites and self.sites:site(x, y, z) or nil
end

-- Could a part of type `partType` set down with `facing` (optional) join this square? Returns true, or false and
-- "unknown_part", "removed" (LiveWater removed from the world), "occupied", "ports_full", or the
-- refusal of a capability (attach, e.g. "no_source"). Changes nothing.
function Topology:canAdd(partType, x, y, z, facing)
    if self.closed and self.closed() then return false, "removed" end
    if not self.catalog:has(partType) then return false, "unknown_part" end
    if self.registry:at(x, y, z) then return false, "occupied" end
    local probe = { type = partType, x = x, y = y, z = z, facing = facing }
    self:recordCuts(probe)
    local ok, reason = self.network:canAdd(probe)
    if not ok then return false, reason end
    return self.catalog:attach({ type = partType }, self:siteAt(x, y, z))
end

local function copy(v)
    if type(v) ~= "table" then return v end
    local out = {}
    for k, x in pairs(v) do out[k] = copy(x) end
    return out
end

-- Add a part. `data` (optional) is the state it brings back (a moveable picked up and set down
-- again, LWT_Placement), copied; `facing` (optional) the facing of the sprite it was set down with,
-- recorded. Returns true and the registry entry, or false and a reason of canAdd.
function Topology:add(partType, x, y, z, data, facing)
    local ok, reason = self:canAdd(partType, x, y, z, facing)
    if not ok then return false, reason end
    local entry = self.registry:add(partType, x, y, z)
    if type(data) == "table" then entry.data = copy(data) end
    entry.facing = facing
    self:recordCuts(entry)
    self.catalog:attach(entry, self:siteAt(x, y, z))
    local _, id = self.network:add(entry)
    self.sprites:around(x, y, z)
    self.events.emit("partAdded", entry)
    self.events.emit("networkChanged", id)
    return true, entry
end

-- Parts of the network of the part on a square (the view of the network, E13), or an empty list.
function Topology:networkOf(x, y, z)
    local id = self.network:networkAt(x, y, z)
    return id and self.network:members(id) or {}
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

-- An edge object (wall, fence) was set down or taken away on a square (ADR-002 D05): the links of
-- the parts of this square and of its N and W neighbours are judged again, sprites follow and
-- every network they now belong to is announced. A link that appears where a port is full is not
-- made: the part placed later stays apart (ADR-006 D05). Returns how many networks were announced.
function Topology:relink(x, y, z)
    local before = self.network:masksAround(x, y, z)
    local squares = { { x, y }, { x, y - 1 }, { x - 1, y } }
    for i = 1, #squares do
        local entry = self.registry:at(squares[i][1], squares[i][2], z)
        if entry then self:recordCuts(entry) end
    end
    local ids = self.network:relink(x, y, z, before)
    if #ids == 0 then return 0 end
    self.sprites:around(x, y, z)
    self.sprites:around(x, y - 1, z)
    self.sprites:around(x - 1, y, z)
    for i = 1, #ids do self.events.emit("networkChanged", ids[i]) end
    return #ids
end

-- No event tells a wall or fence built by a player (only removals and moveables fire one): the
-- clock asks here (a chore). The cuts of every part on a loaded square are judged again; a part
-- whose cuts changed is relinked. Returns how many parts changed.
function Topology:refreshCuts(isLoaded)
    local entries, changed = self.registry:active(), 0
    for i = 1, #entries do
        local e = entries[i]
        if isLoaded(e.x, e.y, e.z) then
            local now = self:cutsAt(e.x, e.y, e.z)
            if now ~= (e.cuts or 0) then
                changed = changed + 1
                local masks = self.network:masksAround(e.x, e.y, e.z)
                e.cuts = now > 0 and now or nil
                local ids = self.network:relink(e.x, e.y, e.z, masks)
                self.sprites:around(e.x, e.y, e.z)
                for j = 1, #ids do self.events.emit("networkChanged", ids[j]) end
            end
        end
    end
    return changed
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
