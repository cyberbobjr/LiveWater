-- LiveWater part "LiveWater:PipeGalvanized": galvanized pipe laid on the ground, one per square,
-- one LiveWater.PipeSection each (ADR-001 D12, Q01). Registered through the public API like any
-- other mod's part. Sprites: tileset batman_livewater_01, index = side mask 0..15
-- (docs/annexes/conception/tuiles-contrat.md).

require "LiveWater/LWT_API"

local TILESET = "batman_livewater_01_"

local sprites = {}
for mask = 0, 15 do sprites[mask] = TILESET .. mask end

LiveWater.API.registerPart("LiveWater:PipeGalvanized", {
    sprites = sprites,
    capabilities = {
        conduit = true,
        layable = { item = "LiveWater.PipeSection", tool = "base:pipewrench" },
    },
})
