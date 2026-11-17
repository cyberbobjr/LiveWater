-- LiveWater source kind "well": a vanilla well on a neighbour square (ADR-001 D24, P02), its water
-- is clean. camping_01_16 is the sprite of the vanilla entity Well (Java 42.22 media,
-- entity_well.txt; tile properties waterAmount 999999). Other wells: another mod registers a
-- source kind with its own sprites (LiveWater.API.registerSource).

return { quality = "clean", sprites = { "camping_01_16" } }
