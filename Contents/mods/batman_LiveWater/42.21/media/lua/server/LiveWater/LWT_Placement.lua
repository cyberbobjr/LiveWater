if isClient() then return end
-- LiveWater: placement and removal of part tiles on the authority (ADR-001 D01, D10). A tile is
-- a part when its sprite belongs to a registered part type (catalog lookup, never a list of
-- names). The composition root (LWT_Server) calls these from OnObjectAdded (vanilla moveable
-- placement, ISMoveableSpriteProps:placeMoveableInternal, solo and server) and
-- OnObjectAboutToBeRemoved (pickup, removal of a square object). No game API here.

local Placement = {}
Placement.__index = Placement

function Placement.new(topology, catalog, log)
    return setmetatable({ topology = topology, catalog = catalog, log = log or print }, Placement)
end

-- A tile with this sprite appeared on a square. Returns true (added, or already known), or
-- false and "not_a_part" or a refusal of the topology ("occupied", "ports_full"), logged:
-- the tile then stays a plain decoration.
function Placement:added(spriteName, x, y, z)
    local partType = self.catalog:typeOfSprite(spriteName)
    if not partType then return false, "not_a_part" end
    local entry = self.topology:at(x, y, z)
    if entry and entry.type == partType then return true end
    local ok, reason = self.topology:add(partType, x, y, z)
    if not ok then
        self.log("LiveWater: " .. partType .. " placed at " .. x .. "," .. y .. "," .. z
            .. " is not connected: " .. tostring(reason))
        return false, reason
    end
    return true
end

-- A tile with this sprite is about to leave a square. Returns true when its part left, or
-- false and "not_a_part" (another object of the square, or nothing registered there).
function Placement:removed(spriteName, x, y, z)
    local partType = self.catalog:typeOfSprite(spriteName)
    local entry = partType and self.topology:at(x, y, z)
    if not entry or entry.type ~= partType then return false, "not_a_part" end
    self.topology:remove(x, y, z)
    return true
end

return Placement
