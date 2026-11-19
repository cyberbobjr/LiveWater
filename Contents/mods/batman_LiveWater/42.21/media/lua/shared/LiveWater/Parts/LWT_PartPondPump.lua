-- LiveWater part "LiveWater:PondPump": electric pump set down next to a water source with the
-- vanilla furniture cursor (moveable Base.Mov_LiveWater_PondPump), ADR-001 D16, D20. Drawn by
-- its state and facing (tileset batman_livewater_01, docs/annexes/conception/tuiles-contrat.md):
-- 24-27 off, 28-31 on; facings S, E, N, W. No filter: it lives in the house water inlet
-- (ADR-005 D01, D02); tiles 32-39 are no longer drawn.

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:PondPump", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ off = 24, on = 28 }),
    capabilities = {
        intake = true,
        pump = { ports = 4, pressure = 6, flow = 50, watts = 250, repairItem = "Base.ScrapMetal", repairCount = 2,
            repairTool = "base:wrench", sound = "GeneratorLoop" },
    },
})
