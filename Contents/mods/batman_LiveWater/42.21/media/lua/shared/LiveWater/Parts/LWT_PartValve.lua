-- LiveWater part "LiveWater:Valve": inline shut-off valve set down between two pipes with the
-- vanilla furniture cursor (moveable Base.Mov_LiveWater_Valve), ADR-001 D02, D13, P11. It lets
-- water through (two pipes at most) while open; closed by hand (right-click), it cuts everything
-- after it. Placed open. Drawn by its state and along its pipe (tileset batman_livewater_01,
-- docs/annexes/conception/tuiles-contrat.md): open 16 east-west, 17 north-south, closed 18, 19;
-- alone or on a bend it keeps the axis it shows.

require "LiveWater/LWT_API"
local Tiles = require "LiveWater/LWT_Tiles"

-- Variant facings follow the tiles' Facing property: 1 = S (the ns tile), 2 = E (the ew tile).
local NS, EW = 1, 2

LiveWater.API.registerPart("LiveWater:Valve", {
    variants = {
        open = { Tiles.sprite(17), Tiles.sprite(16) },
        closed = { Tiles.sprite(19), Tiles.sprite(18) },
    },
    -- side masks (N = 1, E = 2, S = 4, W = 8) of a straight pipe -> facing
    facings = { [2] = EW, [8] = EW, [10] = EW, [1] = NS, [4] = NS, [5] = NS },
    capabilities = {
        conduit = { ports = 2 },
        valve = { open = true, look = true },
        controller = { mode = "manual" },
    },
})
