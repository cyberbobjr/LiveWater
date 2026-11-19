-- LiveWater part "LiveWater:BarrelFitting": barrel fitting set down with the vanilla furniture cursor
-- (moveable Base.Mov_LiveWater_BarrelFitting) between a pipe and a barrel, ADR-001 D26, P02, P17.
-- Its container stands on the square behind it (opposite its facing), else on another side. Set to
-- Fill, the network fills the container; set to Pump, the pumps draw it. Drawn by its mode and the
-- shape of the container (tileset batman_livewater_01, docs/annexes/conception/tuiles-contrat.md):
-- 64-67 Fill into a tall barrel, 68-71 Fill into a low crate collector, 72-75 Pump; facings S, E,
-- N, W. The water goes through it from one pipe to the next (conduit, ADR-008 D01b), and it is
-- drawn branched on the pipes linked in front and on its sides (D01, D01b; the barrel stays behind):
-- bend +1 (side of the next facing) 184/192/200, bend +3 (previous facing) 188/196/204, tee (+1 and
-- +3) 208/224/240, front and +1 212/228/244, front and +3 216/232/248, cross 220/236/252 (Fill tall,
-- Fill low, Pump; facings S, E, N, W).

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:BarrelFitting", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ fill = 64, fill_low = 68, pump = 72,
        fill_bend1 = 184, fill_bend3 = 188, fill_low_bend1 = 192, fill_low_bend3 = 196,
        pump_bend1 = 200, pump_bend3 = 204,
        fill_tee = 208, fill_front1 = 212, fill_front3 = 216, fill_cross = 220,
        fill_low_tee = 224, fill_low_front1 = 228, fill_low_front3 = 232, fill_low_cross = 236,
        pump_tee = 240, pump_front1 = 244, pump_front3 = 248, pump_cross = 252 }),
    -- relative mask of the linked pipes (1 front, 2 side +1, 8 side +3) -> suffix of the variant drawn;
    -- front alone or no pipe: the straight variant
    branches = { [2] = "bend1", [8] = "bend3", [10] = "tee", [3] = "front1", [9] = "front3", [11] = "cross" },
    capabilities = {
        conduit = true,
        fitting = { rate = 50 },
    },
})
