-- LiveWater: sides of a square and their 4-bit mask (pure, no game API).
-- N = 1, E = 2, S = 4, W = 8 (ADR-001 D12); north is -y in Project Zomboid.

local Grid = {}

Grid.N, Grid.E, Grid.S, Grid.W = 1, 2, 4, 8
Grid.ALL = 15

return Grid
