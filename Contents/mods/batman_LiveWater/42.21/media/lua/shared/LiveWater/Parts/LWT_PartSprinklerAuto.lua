-- LiveWater part "LiveWater:SprinklerAuto": automatic sprinkler, the manual sprinkler with a hose
-- timer (recipe LWTUpgradeSprinkler, Electrical 2), moveable Base.Mov_LiveWater_SprinklerAuto,
-- ADR-001 D19, D20. Its timer opens it every 6 hours by default (set on the sprinkler, sandbox bounds)
-- for the time to serve the plants; the timer draws 5 W (Live Wire consumer, or the vanilla rule):
-- without current it triggers nothing; opening it by hand stays possible. Drawn by its state and
-- facing (tileset batman_livewater_01, docs/annexes/conception/tuiles-contrat.md): 56-59 at rest,
-- 60-63 watering (jet frames 80-103 drawn by the clients, D08a); facings S, E, N, W.

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:SprinklerAuto", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ off = 56, on = 60 }),
    capabilities = {
        outlet = { type = "sprinkler" },
        valve = { open = false },
        controller = { mode = "timer", every = 6, watts = 5 },
        spray = { radius = 2, dose = 0.2, jetSheet = Tiles.SHEET, jetFirst = Tiles.JET_FIRST, jetFrames = Tiles.JET_FRAMES },
    },
})
