-- LiveWater part "LiveWater:PondPump": electric pump set down next to a water source with the
-- vanilla furniture cursor (moveable Base.Mov_LiveWater_PondPump), ADR-001 D16, D20. Drawn by
-- its state and facing (tileset batman_livewater_01, docs/annexes/conception/tuiles-contrat.md):
-- 24-27 off, 28-31 on, 32-35 filter on, 36-39 filter off; facings S, E, N, W. A charcoal
-- cartridge (LiveWater.WaterFilter, 500 L) fits in it (D17, Q02).

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:PondPump", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ off = 24, on = 28, filter_on = 32, filter_off = 36 }),
    capabilities = {
        filter = { item = "LiveWater.WaterFilter", capacity = 500 },
        intake = true,
        pump = { ports = 4, pressure = 6, flow = 50, watts = 250, repairItem = "Base.ScrapMetal", repairCount = 2,
            repairTool = "base:wrench", sound = "GeneratorLoop" },
    },
})
