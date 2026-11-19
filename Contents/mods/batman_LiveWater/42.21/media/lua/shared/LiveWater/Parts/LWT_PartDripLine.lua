-- LiveWater part "LiveWater:DripLine": drip line laid on the ground, one per square, set down and
-- picked up like a pipe (moveable Base.Mov_LiveWater_DripLine), ADR-004 D01. Water goes through it
-- (conduit) and leaves it by small emitters: an outlet of type "drip" (any water, clean or not,
-- ADR-005 D03; the drip lines of a network pay one pressure together, D04; like every consumer they
-- need a pump, ADR-012 D03) that
-- waters the squares beside it it is not linked to by 200 ml doses, without loss (drip capability,
-- server LWT_Plants with LWT_DripArea, D02, D03); served, each square draws its flow (sandbox option
-- DripFlow, 0.5 L, ADR-006 D01, D02), the plants take what they need, the rest is lost. Silent (D06). No fence sleeve (ADR-002 D03).
-- Sprites: tileset batman_livewater_01, index = 160 + side mask 0..15
-- (docs/annexes/conception/tuiles-contrat.md).

require "LiveWater/LWT_API"

local TILESET = "batman_livewater_01_"
local FIRST = 160

local sprites = {}
for mask = 0, 15 do sprites[mask] = TILESET .. (FIRST + mask) end

LiveWater.API.registerPart("LiveWater:DripLine", {
    sprites = sprites,
    capabilities = {
        conduit = true,
        outlet = { type = "drip" },
        drip = { dose = 0.2 },
    },
})
