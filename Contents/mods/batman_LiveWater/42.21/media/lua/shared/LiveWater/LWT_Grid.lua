-- LiveWater: sides of a square, their 4-bit mask and square keys (pure, no game API).
-- N = 1, E = 2, S = 4, W = 8 (ADR-001 D12); north is -y in Project Zomboid.

local Grid = {}

Grid.N, Grid.E, Grid.S, Grid.W = 1, 2, 4, 8
Grid.ALL = 15

-- Side each facing 1..4 (S, E, N, W: the order of the variant lists, LWT_Parts) turns to.
Grid.FACINGS = { 4, 2, 1, 8 }

-- Sides in a fixed order (N, E, S, W): bit, offset to the neighbour, bit of the opposite side.
Grid.SIDES = {
    { bit = 1, dx = 0, dy = -1, opposite = 4 },
    { bit = 2, dx = 1, dy = 0, opposite = 8 },
    { bit = 4, dx = 0, dy = 1, opposite = 1 },
    { bit = 8, dx = -1, dy = 0, opposite = 2 },
}

-- Square that carries the edge on `side` of square (x, y), and whether it is its north edge (else its west
-- edge): a square carries only its N and W edges (ADR-002).
function Grid.edgeOf(x, y, side)
    if side == Grid.N then return x, y, true end
    if side == Grid.W then return x, y, false end
    if side == Grid.S then return x, y + 1, true end
    return x + 1, y, false
end

-- Kahlua has no bit library: test one bit of a mask arithmetically.
function Grid.has(mask, bit)
    return math.floor(mask / bit) % 2 == 1
end

-- Key of a square, "x,y,z" (also the index of the persistent registry, D10).
function Grid.key(x, y, z)
    return string.format("%d,%d,%d", x, y, z)
end

return Grid
