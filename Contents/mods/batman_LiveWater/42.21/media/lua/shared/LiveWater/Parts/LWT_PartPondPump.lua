-- LiveWater part "LiveWater:PondPump": electric pump set down next to a water source with the
-- vanilla furniture cursor (moveable Base.Mov_LiveWater_PondPump), ADR-001 D16, D20. Drawn by
-- its state and facing (tileset batman_livewater_01, docs/annexes/conception/tuiles-contrat.md):
-- 24-27 off, 28-31 on, 32-35 filter on, 36-39 filter off; facings S, E, N, W.

require "LiveWater/LWT_API"

local TILESET = "batman_livewater_01_"

-- Variant key -> first index of its four facings.
local FIRST = { off = 24, on = 28, filter_on = 32, filter_off = 36 }

local variants = {}
for key, first in pairs(FIRST) do
    local list = {}
    for facing = 1, 4 do list[facing] = TILESET .. (first + facing - 1) end
    variants[key] = list
end

LiveWater.API.registerPart("LiveWater:PondPump", {
    variants = variants,
    capabilities = {
        intake = true,
        pump = { ports = 4, pressure = 6, flow = 50, watts = 250 },
    },
})
