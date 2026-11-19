if isClient() then return end
-- LiveWater: sprites follow the links of the parts (ADR-001 D11, D12). After a topology change
-- the part and its four neighbours get the sprite of their side mask, applied only when it
-- changed. A type that draws no sprite for a mask keeps the sprite it was placed with (an
-- orientation chosen at placement); a type drawn by its state follows it through `show`, and
-- turns with its pipe when it gives a variant facing for the mask (`facings`, a sprinkler fed by
-- its pipe), else keeps the facing it shows (an inline valve: no `facings`, ADR-008 D08), or takes
-- the shape of the sides it links relative to its facing (`branches`, a barrel fitting).
-- A shape crossing a fence carried by its own N or W edge takes its sleeve sprite when the type
-- draws one (`crossings`, ADR-002 D03); the port says what an edge carries (optional):
--   port:edge(x, y, z, north) -> "wall", "fence" or nil  (N edge when north, else W edge)
-- No game API here: the sprite port is injected:
--   port:spriteOf(x, y, z, typeId)        current sprite of the part object, nil if not found
--   port:setSprite(x, y, z, typeId, name) change and broadcast it (LWT_GameWorld)

local Grid = require "LiveWater/LWT_Grid"

local Sprites = {}
Sprites.__index = Sprites

function Sprites.new(network, catalog, port)
    return setmetatable({ network = network, catalog = catalog, port = port }, Sprites)
end

-- Linked N and W sides of a square that cross a fence carried by the square: 0, 1, 8 or 9.
function Sprites:crossed(x, y, z, mask)
    if not self.port.edge then return 0 end
    local out = 0
    if Grid.has(mask, Grid.N) and self.port:edge(x, y, z, true) == "fence" then out = out + Grid.N end
    if Grid.has(mask, Grid.W) and self.port:edge(x, y, z, false) == "fence" then out = out + Grid.W end
    return out
end

-- Bring the part of one square to its shape. Returns true when its sprite changed.
function Sprites:refresh(x, y, z)
    local part = self.network:part(x, y, z)
    if not part then return false end
    local mask = self.network:mask(x, y, z)
    if not self.catalog:hasShape(part.type, mask) then
        return self.catalog:followsLinks(part.type, mask) and self:show(x, y, z)
    end
    local crossed = self:crossed(x, y, z, mask)
    local want = crossed > 0 and self.catalog:crossing(part.type, mask, crossed) or self.catalog:sprite(part.type, mask)
    local current = self.port:spriteOf(x, y, z, part.type)
    if current == nil or current == want then return false end
    return self.port:setSprite(x, y, z, part.type, want) == true
end

-- Draw the part of a square by its state (variants, Parts:look), facing its pipe when the type
-- gives a facing for its side mask, else keeping the facing it was set down with, shaped by the
-- sides it links when the type gives branches (Parts:branch). Returns true when its sprite changed.
function Sprites:show(x, y, z)
    local part = self.network:part(x, y, z)
    local key = part and self.catalog:look(part)
    if not key then return false end
    local current = self.port:spriteOf(x, y, z, part.type)
    if current == nil then return false end
    local mask = self.network:mask(x, y, z)
    local facing = self.catalog:facingFor(part.type, mask) or self.catalog:facingOf(current)
    local want = self.catalog:variant(part.type, self.catalog:branch(part.type, key, facing, mask), facing)
    if want == nil or want == current then return false end
    return self.port:setSprite(x, y, z, part.type, want) == true
end

-- Refresh a square and its four neighbours. Returns how many sprites changed.
function Sprites:around(x, y, z)
    local changed = self:refresh(x, y, z) and 1 or 0
    for i = 1, #Grid.SIDES do
        local side = Grid.SIDES[i]
        if self:refresh(x + side.dx, y + side.dy, z) then changed = changed + 1 end
    end
    return changed
end

return Sprites
