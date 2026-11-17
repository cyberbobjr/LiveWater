-- LiveWater: which relay tanks an inlet wants (ADR-001 D18, D21). Pure. The engine feeds a plumbed
-- fixture from a water tank on the floor above, on its square or one of the 8 around it
-- (IsoObject.FindExternalWaterSource, Java 42.22): one invisible relay one level above a fixture
-- serves its neighbours too.
-- A fixture is { x, y, z, source }: source = nil (no tank above it), "other" (a tank that is not
-- one of LiveWater's relays: a Live Wire relay, a vanilla barrel, another mod: left alone), or
-- { owner = inlet key, x, y, z } (one of LiveWater's relays).
-- wanted(fixtures, owner) -> { ["x,y,z"] = { x, y, z } }: our relays kept where they are, a new one
-- above each fixture without a tank unless a wanted relay already stands above it or around.

local Grid = require "LiveWater/LWT_Grid"

local RelayPlan = {}

-- Highest level of the map (a relay goes one level above its fixture).
RelayPlan.TOP = 31

local function sharedAbove(wanted, f)
    for dx = -1, 1 do
        for dy = -1, 1 do
            if wanted[Grid.key(f.x + dx, f.y + dy, f.z + 1)] then return true end
        end
    end
    return false
end

local function want(wanted, x, y, z)
    wanted[Grid.key(x, y, z)] = { x = x, y = y, z = z }
end

function RelayPlan.wanted(fixtures, owner)
    local wanted = {}
    for i = 1, #fixtures do
        local f = fixtures[i]
        local src = f.source
        if type(src) == "table" then
            if src.owner == owner then want(wanted, src.x, src.y, src.z) end
        elseif src == nil and f.z < RelayPlan.TOP and not sharedAbove(wanted, f) then
            want(wanted, f.x, f.y, f.z + 1)
        end
    end
    return wanted
end

return RelayPlan
