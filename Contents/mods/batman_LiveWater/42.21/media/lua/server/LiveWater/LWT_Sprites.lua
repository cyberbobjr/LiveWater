if isClient() then return end
-- LiveWater: sprites follow the links of the parts (ADR-001 D11, D12). After a topology change
-- the part and its four neighbours get the sprite of their side mask, applied only when it
-- changed. A type that draws no sprite for a mask keeps the sprite it was placed with (an
-- orientation chosen at placement). No game API here: the sprite port is injected:
--   port:spriteOf(x, y, z, typeId)        current sprite of the part object, nil if not found
--   port:setSprite(x, y, z, typeId, name) change and broadcast it (LWT_GameWorld)

local Grid = require "LiveWater/LWT_Grid"

local Sprites = {}
Sprites.__index = Sprites

function Sprites.new(network, catalog, port)
    return setmetatable({ network = network, catalog = catalog, port = port }, Sprites)
end

-- Bring the part of one square to its shape. Returns true when its sprite changed.
function Sprites:refresh(x, y, z)
    local part = self.network:part(x, y, z)
    if not part then return false end
    local mask = self.network:mask(x, y, z)
    if not self.catalog:hasShape(part.type, mask) then return false end
    local want = self.catalog:sprite(part.type, mask)
    local current = self.port:spriteOf(x, y, z, part.type)
    if current == nil or current == want then return false end
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
