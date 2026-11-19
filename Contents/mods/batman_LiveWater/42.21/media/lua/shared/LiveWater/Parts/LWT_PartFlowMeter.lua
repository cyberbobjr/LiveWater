-- LiveWater part "LiveWater:FlowMeter": water meter set inline on a pipe with the vanilla
-- furniture cursor (moveable Base.Mov_LiveWater_FlowMeter), ADR-001 D24, P12. It lets water
-- through (two pipes at most) and records the litres of each step; its menu shows them.
-- Drawn along the axis chosen at placement (tileset batman_livewater_01,
-- docs/annexes/conception/tuiles-contrat.md): 20 east-west, 21 north-south. It links only on the
-- two sides of that axis (ADR-008 D08): a pipe set down on a flank stays apart.

require "LiveWater/LWT_API"
local Grid = require "LiveWater/LWT_Grid"
local Tiles = require "LiveWater/LWT_Tiles"

-- Variant facings follow the tiles' Facing property: 1 = S (the ns tile), 2 = E (the ew tile).
local NS, EW = 1, 2

LiveWater.API.registerPart("LiveWater:FlowMeter", {
    -- one look (no state drawn): the tile it was set down with
    variants = { straight = { Tiles.sprite(21), Tiles.sprite(20) } },
    sidesByFacing = { [NS] = Grid.N + Grid.S, [EW] = Grid.E + Grid.W },
    capabilities = {
        conduit = { ports = 2 },
        meter = true,
    },
})
