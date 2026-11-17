-- LiveWater part "LiveWater:HouseInlet": the house water inlet, set down with the vanilla furniture
-- cursor (moveable Base.Mov_LiveWater_HouseInlet) against an exterior wall, ADR-001 D18. Water
-- leaves the network there into invisible relay tanks above the plumbed fixtures of the building
-- it touches (server LWT_Relays). Drawn by its state and facing (tileset batman_livewater_01,
-- docs/annexes/conception/tuiles-contrat.md): 40-43 filtered (green light), 44-47 unfiltered
-- (amber light, D17); facings S, E, N, W.

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:HouseInlet", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ filtered = 40, unfiltered = 44 }),
    capabilities = {
        outlet = { type = "houseInlet" },
    },
})
