-- LiveWater part "LiveWater:HouseInlet": the house water inlet, set down with the vanilla furniture
-- cursor (moveable Base.Mov_LiveWater_HouseInlet) against an exterior wall, ADR-001 D18. Water
-- leaves the network there into invisible relay tanks above the plumbed fixtures of the building
-- it touches (server LWT_Relays). Drawn by its state and facing (tileset batman_livewater_01,
-- docs/annexes/conception/tuiles-contrat.md): 40-43 filtered (green light), 44-47 unfiltered
-- (amber light, D17); with a filter cartridge fitted, 176-179 green, 180-183 amber (worn
-- cartridge); facings S, E, N, W. The charcoal cartridge (LiveWater.WaterFilter, 500 L) fits in
-- it and cleans only the water the house takes (ADR-005 D01, D04); worn out, it comes back as
-- LiveWater.WaterFilterSpent (ADR-009 D01).
-- Look keys (LWT_Parts:look joins the capability tokens in kind order): filter ("filter" while
-- a cartridge is in) then outlet ("filtered" or "unfiltered").

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:HouseInlet", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ filtered = 40, unfiltered = 44, filter_filtered = 176, filter_unfiltered = 180 }),
    capabilities = {
        filter = { item = "LiveWater.WaterFilter", spent = "LiveWater.WaterFilterSpent", capacity = 500 },
        outlet = { type = "houseInlet" },
    },
})
