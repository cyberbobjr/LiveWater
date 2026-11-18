if isClient() then return end
-- LiveWater: barrel fittings on the authority (ADR-001 D26, P02, P17, L08). Chore of the clock and
-- handler of the outlet type "barrelFill" (LWT_Outlets):
--   tick()                         before the networks: every fitting on a loaded square senses its
--                                  container (`sense` hook: fluid, amount, free room, shape) and is
--                                  presented (its sprite follows its mode and the shape)
--   need(part)                     set to Fill: the container's free room, at most the fitting's rate
--   deliver(part, litres, quality) the litres go into the container (water, tainted water or fuel)
--   drawn(part, litres)            set to Pump: the pumps took those litres (event waterDrawn)
-- The container stands on the square behind the fitting (opposite its facing: a fitting facing S
-- has its pipe on the S side and the barrel on the N side, tile builder), else on the first other
-- side that holds one. No game API here; dependencies are injected: { catalog, registry (active()),
-- world (isLoaded, spriteOf), containers (port, LWT_GameContainers: at(x, y, z) -> { fluid, amount,
-- free, sprite, entity } or nil; add(x, y, z, litres, quality); take(x, y, z, litres)), shapes
-- (LWT_Containers), publisher (optional: present(part)) }.

local Fittings = {}
Fittings.__index = Fittings

-- Facing (1..4: S, E, N, W) -> offset of the square behind it.
local BEHIND = { { 0, -1 }, { -1, 0 }, { 0, 1 }, { 1, 0 } }

function Fittings.new(deps)
    return setmetatable({ catalog = deps.catalog, registry = deps.registry, world = deps.world,
        containers = deps.containers, shapes = deps.shapes, publisher = deps.publisher }, Fittings)
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
    for i = 1, #list do
        local x, y, z = part.x + list[i][1], part.y + list[i][2], part.z
        local c = self.containers:at(x, y, z)
        if c then
            return { found = true, fluid = c.fluid, amount = c.amount, free = c.free,
                shape = self.shapes:shapeOf(c.sprite, c.entity), cx = x, cy = y, cz = z }
        end
    end
    return { found = false }
end

function Fittings:tick()
    local parts = self.registry:active()
    for i = 1, #parts do
        local part = parts[i]
        if self:isFitting(part) and self.world:isLoaded(part.x, part.y, part.z) then
            self.catalog:call(part, "sense", self:look(part))
            if self.publisher then self.publisher:present(part) end
        end
    end
end

-- Mode, sensed state and rate of a fitting.
local function stateOf(self, part)
    local mode, d, rate = self.catalog:first(part, "fittingMode")
    return mode, d or {}, rate or 0
end

function Fittings:need(part)
    local mode, d, rate = stateOf(self, part)
    if mode ~= "fill" or not d.found then return 0 end
    return math.max(0, math.min(d.free or 0, rate))
end

function Fittings:deliver(part, litres, quality)
    local mode, d = stateOf(self, part)
    if mode ~= "fill" or not d.found then return end
    self.containers:add(d.cx, d.cy, d.cz, litres, quality)
end

function Fittings:drawn(part, litres)
    local mode, d = stateOf(self, part)
    if mode ~= "pump" or not d.found then return end
    self.containers:take(d.cx, d.cy, d.cz, litres)
end

return Fittings
