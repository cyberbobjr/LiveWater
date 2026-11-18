-- LiveWater: sprite names of the tileset batman_livewater_01 (docs/annexes/conception/tuiles-contrat.md).
-- Shared by the part files; pure.

local Tiles = {}

Tiles.SHEET = "batman_livewater_01_"

-- Jet frames of the sprinklers (D08a): frame f, facing k at index JET_FIRST + 4 * f + k.
Tiles.JET_FIRST = 80
Tiles.JET_FRAMES = 6

-- `facings` of a part fed over one edge of its tile (the S edge when it faces S, e.g. the sprinklers):
-- side mask of its one pipe (N = 1, E = 2, S = 4, W = 8) -> facing (1 S, 2 E, 3 N, 4 W) that turns
-- the feed towards that pipe.
Tiles.FEED_FACINGS = { [1] = 3, [2] = 2, [4] = 1, [8] = 4 }

-- Sprite name of a tile index.
function Tiles.sprite(index)
    return Tiles.SHEET .. index
end

-- `variants` of a part drawn by state and facing: { [key] = { S, E, N, W } } from
-- { [key] = first index of its four facings }.
function Tiles.variants(firstByKey)
    local out = {}
    for key, first in pairs(firstByKey) do
        local list = {}
        for facing = 1, 4 do list[facing] = Tiles.sprite(first + facing - 1) end
        out[key] = list
    end
    return out
end

return Tiles
