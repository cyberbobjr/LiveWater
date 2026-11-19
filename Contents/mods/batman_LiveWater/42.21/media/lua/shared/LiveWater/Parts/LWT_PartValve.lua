-- LiveWater part "LiveWater:Valve": inline shut-off valve set down between two pipes with the
-- vanilla furniture cursor (moveable Base.Mov_LiveWater_Valve), ADR-001 D02, D13, P11. It lets
-- water through (two pipes at most) while open; closed by hand (right-click), it cuts everything
-- after it. Placed open. Drawn by its state along the axis chosen at placement (tileset
-- batman_livewater_01, docs/annexes/conception/tuiles-contrat.md): open 16 east-west, 17
-- north-south, closed 18, 19. It links only on the two sides of that axis (ADR-008 D08): a pipe
-- set down on a flank stays apart, and opening or closing it never turns it.

require "LiveWater/LWT_API"
local Grid = require "LiveWater/LWT_Grid"
local Tiles = require "LiveWater/LWT_Tiles"

-- Variant facings follow the tiles' Facing property: 1 = S (the ns tile), 2 = E (the ew tile).
local NS, EW = 1, 2

LiveWater.API.registerPart("LiveWater:Valve", {
    variants = {
        open = { Tiles.sprite(17), Tiles.sprite(16) },
        closed = { Tiles.sprite(19), Tiles.sprite(18) },
    },
    sidesByFacing = { [NS] = Grid.N + Grid.S, [EW] = Grid.E + Grid.W },
    capabilities = {
        conduit = { ports = 2 },
        valve = { open = true, look = true },
        controller = { mode = "manual" },
    },
})
