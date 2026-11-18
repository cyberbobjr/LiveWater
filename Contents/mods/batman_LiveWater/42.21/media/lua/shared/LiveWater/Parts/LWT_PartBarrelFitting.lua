-- LiveWater part "LiveWater:BarrelFitting": barrel fitting set down with the vanilla furniture cursor
-- (moveable Base.Mov_LiveWater_BarrelFitting) between a pipe and a barrel, ADR-001 D26, P02, P17.
-- Its container stands on the square behind it (opposite its facing), else on another side. Set to
-- Fill, the network fills the container; set to Pump, the pumps draw it. Drawn by its mode and the
-- shape of the container (tileset batman_livewater_01, docs/annexes/conception/tuiles-contrat.md):
-- 64-67 Fill into a tall barrel, 68-71 Fill into a low crate collector, 72-75 Pump; facings S, E,
-- N, W.

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:BarrelFitting", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ fill = 64, fill_low = 68, pump = 72 }),
    capabilities = {
        fitting = { rate = 50 },
    },
})
