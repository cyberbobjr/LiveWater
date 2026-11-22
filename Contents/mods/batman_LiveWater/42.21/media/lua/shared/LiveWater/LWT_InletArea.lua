-- LiveWater: the squares a house inlet serves (ADR-001 D18). Pure: the place is asked through a
-- probe (LWT_GamePlumbing in game, a double in tests):
--   probe:building(x, y, z) -> the map building the inlet touches (its square or one of the 4
--       around), or nil: { x1, y1, x2, y2 (bounds, inclusive), minLevel, maxLevel,
--       contains(self, x, y, z) }
-- Building mode: the squares of that building within `ranges.building` squares of the inlet (a
-- circle), from its lowest level up to the last level of the map (ADR-023 D01: no limit upwards;
-- the building ends where its rooms end); below ground, down to BASEMENT_LEVELS, every square
-- under its ground floor footprint (P18: a basement belongs to the building above it, part of it
-- or not); above ground, also every square above a room of the building: its roof and the storeys
-- the players built on top (ADR-024 D03).
-- Base mode (L11), when the inlet touches no map building (a base the players built): every square
-- within `ranges.base` squares, from the inlet's level up to the last level of the map.
-- In base mode, a fixture of a map building (its original sinks, flagged mapBuilding by the probe)
-- is never taken: after the city water shut-off the circle would otherwise put relays over a
-- neighbour's house; one already fed by a relay of this inlet keeps it.
-- An area: { mode, x, y, z, range, minX, maxX, minY, maxY, minZ, maxZ, contains(self, x, y, z),
-- serves(self, fixture, owner) }.

local Grid = require "LiveWater/LWT_Grid"

local InletArea = {}
InletArea.__index = InletArea

InletArea.BASEMENT_LEVELS = 2

local function inCircle(area, x, y)
    local dx, dy = x - area.x, y - area.y
    return dx * dx + dy * dy <= area.range * area.range
end

function InletArea:contains(x, y, z)
    if z < self.minZ or z > self.maxZ or not inCircle(self, x, y) then return false end
    return self:holds(x, y, z)
end

-- May the inlet `owner` (key) serve this fixture { x, y, z, source, mapBuilding } of its area?
function InletArea:serves(fixture, owner)
    if self.mode ~= "base" or not fixture.mapBuilding then return true end
    local src = fixture.source
    return type(src) == "table" and src.owner == owner
end

local function new(fields)
    return setmetatable(fields, InletArea)
end

-- Is the square above a room of the building `b` (its roof, a storey built on top of it)?
local function above(b, x, y, z)
    for level = math.min(z - 1, b.maxLevel), math.max(b.minLevel, 0), -1 do
        if b:contains(x, y, level) then return true end
    end
    return false
end

-- Area of the map building `b` around an inlet at (x, y, z).
function InletArea.building(b, x, y, z, range)
    local area = new({ mode = "building", x = x, y = y, z = z, range = range,
        minX = math.max(b.x1, x - range), maxX = math.min(b.x2, x + range),
        minY = math.max(b.y1, y - range), maxY = math.min(b.y2, y + range),
        minZ = math.min(b.minLevel, z, -InletArea.BASEMENT_LEVELS), maxZ = Grid.TOP })
    function area:holds(fx, fy, fz)
        return b:contains(fx, fy, fz) or (fz < 0 and b:contains(fx, fy, 0)) or above(b, fx, fy, fz)
    end
    return area
end

-- Area of a player's base around an inlet at (x, y, z).
function InletArea.base(x, y, z, range)
    local area = new({ mode = "base", x = x, y = y, z = z, range = range,
        minX = x - range, maxX = x + range, minY = y - range, maxY = y + range,
        minZ = z, maxZ = Grid.TOP })
    function area:holds()
        return true
    end
    return area
end

-- Area served by an inlet at (x, y, z). ranges = { building = squares, base = squares }.
function InletArea.of(probe, x, y, z, ranges)
    local b = probe:building(x, y, z)
    if b then return InletArea.building(b, x, y, z, ranges.building) end
    return InletArea.base(x, y, z, ranges.base)
end

return InletArea
