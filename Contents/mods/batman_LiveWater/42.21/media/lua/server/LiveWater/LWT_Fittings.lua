if isClient() then return end
-- LiveWater: barrel fittings on the authority (ADR-001 D26, P02, P17, L08). Chore of the clock and
-- handler of the outlet type "barrelFill" (LWT_Outlets):
--   tick()                         before the networks: every fitting on a loaded square senses its
--                                  container (`sense` hook: fluid, amount, free room, shape, share)
--                                  and is presented (its sprite follows its mode and the shape)
--   chunkLoaded(x, y, size)        the squares x..x+size-1, y..y+size-1 were loaded: a fitting
--                                  counted while away there writes its count to its container
--   need(part)                     set to Fill: the container's free room not yet promised this tick
--                                  to another fitting on it, at most the fitting's rate
--   deliver(part, litres, quality) the litres go into the container: water of any quality goes in
--                                  tainted (ADR-005 D07: the network carries impure water except
--                                  in the house), fuel stays fuel
--   drawn(part, litres)            set to Pump: the pumps took those litres (event waterDrawn); the
--                                  fittings sense their containers again (another network steps next)
-- While the square of a fitting or of its container is not loaded (ADR-006 D06), the fitting keeps
-- the content its last sense recorded and counts in it what the network takes (Pump: never more
-- than the recorded amount) or puts (Fill: never more than the recorded free room); the count
-- (`offline`) is written to the real container once, before the first sense on a loaded square
-- (chunk loaded, else the next step): taken then added, never more than the container holds or
-- has room for, so no water is ever created.
-- Two fittings on one container never count the same litres twice: those set to Pump share its
-- amount (`share`, what each may give), those set to Fill share its free room.
-- The container stands on the square behind the fitting (opposite its facing: a fitting facing S
-- has its pipe on the S side and the barrel on the N side, tile builder), else on the first other
-- side that holds one. No game API here; dependencies are injected: { catalog, registry (active()),
-- world (isLoaded, spriteOf), containers (port, LWT_GameContainers: at(x, y, z) -> { fluid, amount,
-- free, sprite, entity } or nil; add(x, y, z, litres, quality); take(x, y, z, litres)), shapes
-- (LWT_Containers: shape), listed (optional: function() -> set of the names of
-- the sandbox option FillContainers), publisher (optional: present(part)) }.

local Flow = require "LiveWater/LWT_Flow"
local Grid = require "LiveWater/LWT_Grid"

local Fittings = {}
Fittings.__index = Fittings

-- Facing (1..4: S, E, N, W) -> offset of the square behind it.
local BEHIND = { { 0, -1 }, { -1, 0 }, { 0, 1 }, { 1, 0 } }
local EPSILON = 0.000001

function Fittings.new(deps)
    return setmetatable({ catalog = deps.catalog, registry = deps.registry, world = deps.world,
        containers = deps.containers, shapes = deps.shapes, listed = deps.listed, publisher = deps.publisher,
        promised = {}, pending = {} }, Fittings)
end

function Fittings:isFitting(part)
    return self.catalog:hasHook(part.type, "sense")
end

-- Squares where the container of a fitting may stand, the one behind first.
function Fittings:candidates(part)
    local sprite = self.world:spriteOf(part.x, part.y, part.z, part.type)
    local facing = sprite and self.catalog:facingOf(sprite) or 1
    local list = { BEHIND[facing] }
    for i = 1, #BEHIND do
        if i ~= facing then list[#list + 1] = BEHIND[i] end
    end
    return list
end

-- What the container of a fitting holds now (the `sense` info).
function Fittings:look(part)
    local list = self:candidates(part)
    local listed = self.listed and self.listed() or {}
    for i = 1, #list do
        local x, y, z = part.x + list[i][1], part.y + list[i][2], part.z
        local c = self.containers:at(x, y, z)
        if c then
            return { found = true, fluid = c.fluid, amount = c.amount, free = c.free,
                shape = self.shapes:shapeOf(c.sprite, c.entity, listed), cx = x, cy = y, cz = z }
        end
    end
    return { found = false }
end

-- Mode, sensed state and rate of a fitting.
local function stateOf(self, part)
    local mode, d, rate = self.catalog:first(part, "fittingMode")
    return mode, d or {}, rate or 0
end

local function containerKey(info)
    return info.cx .. "," .. info.cy .. "," .. info.cz
end

-- Are the square of the fitting and the square of its recorded container loaded?
function Fittings:isLoaded(part)
    if not self.world:isLoaded(part.x, part.y, part.z) then return false end
    local _, d = stateOf(self, part)
    return not d.cx or self.world:isLoaded(d.cx, d.cy, d.cz)
end

-- The count kept while away goes to the real container, once (the next sense clears it).
function Fittings:settle(part)
    local _, d = stateOf(self, part)
    local off = d.offline
    self.pending[Grid.key(part.x, part.y, part.z)] = nil
    if not off or not d.cx then return end
    if (off.taken or 0) > 0 then self.containers:take(d.cx, d.cy, d.cz, off.taken) end
    if (off.added or 0) > 0 and off.quality then self.containers:add(d.cx, d.cy, d.cz, off.added, off.quality) end
end

-- Record of a fitting away after `taken` litres left its container and `added` came in.
function Fittings:count(part, taken, added, quality)
    local _, d = stateOf(self, part)
    local off = d.offline or {}
    local amount = (d.amount or 0) - taken + added
    local info = { found = true, shape = d.shape, fluid = quality or d.fluid, amount = amount,
        free = (d.free or 0) + taken - added, share = d.share and math.max(0, d.share - taken) or nil,
        cx = d.cx, cy = d.cy, cz = d.cz,
        offline = { taken = (off.taken or 0) + taken, added = (off.added or 0) + added, quality = quality or off.quality } }
    if amount <= EPSILON then info.fluid = nil end
    self.catalog:call(part, "sense", info)
    self.pending[Grid.key(part.x, part.y, part.z)] = part
end

-- Every fitting on a loaded square senses its container (after writing the count it kept while
-- away); the amount of a container is shared between the fittings set to Pump on it. Returns the
-- fittings sensed.
function Fittings:senseAll()
    local parts, sensed, infos, pumping = self.registry:active(), {}, {}, {}
    for i = 1, #parts do
        local part = parts[i]
        if self:isFitting(part) and self:isLoaded(part) then
            self:settle(part)
            local info = self:look(part)
            sensed[#sensed + 1], infos[#sensed + 1] = part, info
            if info.found and stateOf(self, part) == "pump" then
                local key = containerKey(info)
                pumping[key] = (pumping[key] or 0) + 1
            end
        end
    end
    for i = 1, #sensed do
        local info = infos[i]
        if info.found then info.share = (info.amount or 0) / (pumping[containerKey(info)] or 1) end
        self.catalog:call(sensed[i], "sense", info)
    end
    return sensed
end

function Fittings:tick()
    self.promised = {}
    local sensed = self:senseAll()
    if not self.publisher then return end
    for i = 1, #sensed do self.publisher:present(sensed[i]) end
end

local function inside(part, d, x1, y1, x2, y2)
    local function within(x, y) return x ~= nil and x >= x1 and x <= x2 and y >= y1 and y <= y2 end
    return within(part.x, part.y) or within(d.cx, d.cy)
end

-- Only the fittings counted while away are looked at (pending), never the whole registry.
function Fittings:chunkLoaded(x, y, size)
    local x2, y2, found, settled = x + size - 1, y + size - 1, false, {}
    for key, part in pairs(self.pending) do
        local _, d = stateOf(self, part)
        if not d.offline then
            settled[#settled + 1] = key
        elseif inside(part, d, x, y, x2, y2) then
            found = true
        end
    end
    for i = 1, #settled do self.pending[settled[i]] = nil end
    if found then self:senseAll() end
end

function Fittings:need(part)
    local mode, d, rate = stateOf(self, part)
    if mode ~= "fill" or not d.found then return 0 end
    local key = containerKey(d)
    local litres = math.max(0, math.min((d.free or 0) - (self.promised[key] or 0), rate))
    self.promised[key] = (self.promised[key] or 0) + litres
    return litres
end

function Fittings:deliver(part, litres, quality)
    local mode, d = stateOf(self, part)
    if mode ~= "fill" or not d.found then return end
    if Flow.family(quality) == "water" then quality = Flow.TAINTED end
    if not self:isLoaded(part) then
        self:count(part, 0, math.max(0, math.min(litres, d.free or 0)), quality)
        return
    end
    self.containers:add(d.cx, d.cy, d.cz, litres, quality)
end

function Fittings:drawn(part, litres)
    local mode, d = stateOf(self, part)
    if mode ~= "pump" or not d.found then return end
    if not self:isLoaded(part) then
        self:count(part, math.max(0, math.min(litres, d.amount or 0)), 0, nil)
        return
    end
    self.containers:take(d.cx, d.cy, d.cz, litres)
    self:senseAll()
end

return Fittings
