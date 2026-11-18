-- LiveWater part "LiveWater:Sprinkler": manual sprinkler set down with the vanilla furniture cursor
-- (moveable Base.Mov_LiveWater_Sprinkler), ADR-001 D19, P13, P14. Placed closed; opened and closed
-- by hand (right-click). Open, it waters the plants that need it within its radius (2 squares,
-- times the sandbox option SprinklerRadiusMultiplier) by 200 ml doses taken from the network
-- (server LWT_Plants). Drawn by its state and facing (tileset batman_livewater_01,
-- docs/annexes/conception/tuiles-contrat.md): 48-51 off, 52-55 on (without the jet: the clients
-- draw the jet frames 80-103 on top, D08a); facings S, E, N, W. While it waters the players hear the
-- vanilla watering sound (P14).

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

LiveWater.API.registerPart("LiveWater:Sprinkler", {
    -- variant key -> first index of its four facings
    variants = Tiles.variants({ off = 48, on = 52 }),
    capabilities = {
        outlet = { type = "sprinkler" },
        valve = { open = false },
        controller = { mode = "manual" },
        spray = { radius = 2, dose = 0.2, jetSheet = Tiles.SHEET, jetFirst = Tiles.JET_FIRST,
            jetFrames = Tiles.JET_FRAMES, sound = "WaterCrops" },
    },
})
