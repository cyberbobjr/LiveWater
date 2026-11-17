-- LiveWater part "LiveWater:FlowMeter": water meter set inline on a pipe with the vanilla
-- furniture cursor (moveable Base.Mov_LiveWater_FlowMeter), ADR-001 D24, P12. It lets water
-- through (two pipes at most) and records the litres of each step; its menu shows them.
-- Drawn along its pipe (tileset batman_livewater_01, docs/annexes/conception/tuiles-contrat.md):
-- 20 east-west, 21 north-south; alone or on a bend it keeps the sprite it was set down with.

require "LiveWater/LWT_API"

local EW, NS = "batman_livewater_01_20", "batman_livewater_01_21"

LiveWater.API.registerPart("LiveWater:FlowMeter", {
    -- side masks (N = 1, E = 2, S = 4, W = 8) of a straight pipe
    sprites = { [2] = EW, [8] = EW, [10] = EW, [1] = NS, [4] = NS, [5] = NS },
    capabilities = {
        conduit = { ports = 2 },
        meter = true,
    },
})
