-- LiveWater: squares a drip line waters (ADR-004 D02). Pure, no game API. Each square of the line
-- waters its neighbours N, E, S, W it is not linked to (a straight line waters the squares on each
-- side, its loose end the square past it); never its own square.

local Grid = require "LiveWater/LWT_Grid"

local Area = {}

-- Neighbours of (x, y) on the sides not in `mask` (the side mask of its links): list of { x, y, d2 }.
function Area.squares(x, y, mask)
    local out = {}
    for i = 1, #Grid.SIDES do
        local side = Grid.SIDES[i]
        if not Grid.has(mask, side.bit) then out[#out + 1] = { x = x + side.dx, y = y + side.dy, d2 = 1 } end
    end
    return out
end

-- Area strategy of LWT_Plants for the drip parts: function(part) -> squares, litres of a dose (`drip`
-- hook), share lost (none, D03) and litres the square draws per step (ADR-006 D01, D02; `scale`
-- optional, function(optionName) -> sandbox value). The links come from the network graph.
function Area.reach(catalog, network, scale)
    local ctx = { scale = scale }
    return function(part)
        local dose, flow = catalog:first(part, "drip", ctx)
        if not dose then return {}, 0, 0, 0 end
        return Area.squares(part.x, part.y, network:mask(part.x, part.y, part.z)), dose, 0, flow or 0
    end
end

return Area
