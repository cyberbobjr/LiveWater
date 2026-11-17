-- LiveWater: sprite names of the tileset batman_livewater_01 (docs/annexes/conception/tuiles-contrat.md).
-- Shared by the part files; pure.

local Tiles = {}

Tiles.SHEET = "batman_livewater_01_"

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
