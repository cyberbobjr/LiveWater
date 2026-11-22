-- LiveWater source kind "well": a vanilla well on a neighbour square (ADR-001 D24, P02), its water
-- is clean. camping_01_16 is the sprite of the vanilla entity Well (Java 42.22 media,
-- entity_well.txt); camping_01_64 to 67 are the four facings of the vanilla metal hand pump
-- (ADR-025). All five carry the tile properties waterAmount and waterMaxAmount 999999 and no
-- taintedWater. Other wells: another mod registers a source kind with its own sprites
-- (LiveWater.API.registerSource).

return {
    quality = "clean",
    sprites = { "camping_01_16", "camping_01_64", "camping_01_65", "camping_01_66", "camping_01_67" },
}
