-- LiveWater part "LiveWater:BarrelFitting": barrel fitting set down with the vanilla furniture cursor
-- (moveable Base.Mov_LiveWater_BarrelFitting) between a pipe and a barrel, ADR-001 D26, P02, P17.
-- Its container stands on the square behind it (opposite its facing), else on another side. The
-- network fills the container (Fill only, ADR-012 D02). Drawn by the shape of the container (tileset
-- batman_livewater_01, docs/annexes/conception/tuiles-contrat.md): 64-67 into a tall barrel, 68-71
-- into a low crate collector; facings S, E, N, W. The water goes through it from one pipe to the
-- next (conduit, ADR-008 D01b), and it is drawn branched on the pipes linked in front and on its
-- sides (D01, D01b; the barrel stays behind): bend +1 (side of the next facing) 184/192, bend +3
-- (previous facing) 188/196, tee (+1 and +3) 208/224, front and +1 212/228, front and +3 216/232,
-- cross 220/236 (tall, low; facings S, E, N, W). The tiles of the former Pump mode (72-75, 200-207,
-- 240-255) stay in the tileset, unused.

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:BarrelFitting", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ fill = 64, fill_low = 68,
        fill_bend1 = 184, fill_bend3 = 188, fill_low_bend1 = 192, fill_low_bend3 = 196,
        fill_tee = 208, fill_front1 = 212, fill_front3 = 216, fill_cross = 220,
        fill_low_tee = 224, fill_low_front1 = 228, fill_low_front3 = 232, fill_low_cross = 236 }),
    -- relative mask of the linked pipes (1 front, 2 side +1, 8 side +3) -> suffix of the variant drawn;
    -- front alone or no pipe: the straight variant
    branches = { [2] = "bend1", [8] = "bend3", [10] = "tee", [3] = "front1", [9] = "front3", [11] = "cross" },
    capabilities = {
        conduit = true,
        fitting = { rate = 50 },
    },
})
