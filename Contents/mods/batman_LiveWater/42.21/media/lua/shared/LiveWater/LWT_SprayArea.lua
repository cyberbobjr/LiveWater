-- LiveWater: squares a sprinkler waters (ADR-003 D01), shared by the authority (LWT_Plants) and the
-- client (watered area highlight, D02). Pure, no game API. The area is the square of `radius`
-- squares on each axis around the sprinkler (Chebyshev distance), radius 2 -> 5 x 5.

local Area = {}

-- Squares of the area around (x, y): list of { x, y, d2 } (d2 = squared distance, for a
-- nearest-first order), row by row.
function Area.squares(x, y, radius)
    local out = {}
    for dx = -radius, radius do
        for dy = -radius, radius do
            out[#out + 1] = { x = x + dx, y = y + dy, d2 = dx * dx + dy * dy }
        end
    end
    return out
end

-- Area strategy of LWT_Plants for the parts that spray: function(part) -> squares of its radius,
-- litres of a dose, share of the water drawn lost in the air and litres drawn per step (`spray`
-- hook, read with the sandbox values of `scale`, function(optionName) -> value; ADR-006 D01, D02).
function Area.reach(catalog, scale)
    local ctx = { scale = scale }
    return function(part)
        local radius, dose, loss, flow = catalog:first(part, "spray", ctx)
        if not radius then return {}, 0, 0, 0 end
        return Area.squares(part.x, part.y, radius), dose, loss or 0, flow or 0
    end
end

return Area
