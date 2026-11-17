-- LiveWater: the squares a house inlet serves (ADR-001 D18). Pure: the place is asked through a
-- probe (LWT_GamePlumbing in game, a double in tests):
--   probe:building(x, y, z) -> the map building the inlet touches (its square or one of the 4
--       around), or nil: { x1, y1, x2, y2 (bounds, inclusive), minLevel, maxLevel,
--       contains(self, x, y, z) }
-- Building mode: the squares of that building within `ranges.building` squares of the inlet (a
-- circle), from its lowest level up to LEVELS_UP floors above the inlet.
-- An area: { mode, x, y, z, range, minX, maxX, minY, maxY, minZ, maxZ, contains(self, x, y, z) }.

local InletArea = {}
InletArea.__index = InletArea

InletArea.LEVELS_UP = 3

local function inCircle(area, x, y)
    local dx, dy = x - area.x, y - area.y
    return dx * dx + dy * dy <= area.range * area.range
end

function InletArea:contains(x, y, z)
    if z < self.minZ or z > self.maxZ or not inCircle(self, x, y) then return false end
    return self:holds(x, y, z)
end

local function new(fields)
    return setmetatable(fields, InletArea)
end

-- Area of the map building `b` around an inlet at (x, y, z).
function InletArea.building(b, x, y, z, range)
    local area = new({ mode = "building", x = x, y = y, z = z, range = range,
        minX = math.max(b.x1, x - range), maxX = math.min(b.x2, x + range),
        minY = math.max(b.y1, y - range), maxY = math.min(b.y2, y + range),
        minZ = math.min(b.minLevel, z), maxZ = z + InletArea.LEVELS_UP })
    function area:holds(fx, fy, fz)
        return b:contains(fx, fy, fz)
    end
    return area
end

-- Area served by an inlet at (x, y, z). ranges = { building = squares }.
function InletArea.of(probe, x, y, z, ranges)
    local b = probe:building(x, y, z)
    if b then return InletArea.building(b, x, y, z, ranges.building) end
    return nil
end

return InletArea
