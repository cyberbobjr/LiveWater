-- LiveWater part "LiveWater:PipeGalvanized": galvanized pipe on the ground, one per square, set
-- down and picked up like the other parts: moveable Base.Mov_LiveWater_Pipe (ADR-001 D12, Q01
-- updated 2026-11-18). Registered through the public API like any
-- other mod's part. Sprites: tileset batman_livewater_01, index = side mask 0..15
-- (docs/annexes/conception/tuiles-contrat.md).

require "LiveWater/LWT_API"

local TILESET = "batman_livewater_01_"

local sprites = {}
for mask = 0, 15 do sprites[mask] = TILESET .. mask end

-- Pipes crossing a fence carried by their own N edge (1), W edge (8) or both (9), ADR-002 D03:
-- from index 104, masks in ascending order, for each N, then W, then both (tuiles-contrat.md).
local N, W = 1, 8
local function has(mask, bit) return math.floor(mask / bit) % 2 == 1 end
local crossings, index = {}, 104
for mask = 0, 15 do
    for _, edges in ipairs({ N, W, N + W }) do
        if (edges ~= W or has(mask, W)) and (edges ~= N or has(mask, N)) and (edges ~= N + W or (has(mask, N) and has(mask, W))) then
            crossings[mask] = crossings[mask] or {}
            crossings[mask][edges] = TILESET .. index
            index = index + 1
        end
    end
end

LiveWater.API.registerPart("LiveWater:PipeGalvanized", {
    sprites = sprites,
    crossings = crossings,
    capabilities = {
        conduit = true,
    },
})
