-- LiveWater: game adapter of the in-world dismantling (ADR-007 D02). Declares one vanilla scrap material
-- LiveWater<name> per placeable part of the table LWT_Dismantle (tiles: CanScrap, Material, ScrapSize),
-- with the tools, skill and items of its inventory recipe.
--
-- Order: vanilla ISMoveableDefinitions.load (shared/Moveables, registered on OnGameBoot when the vanilla
-- files run, before any mod file) resets every definition, so this handler, registered later, runs after it.
-- The game multiplies a returned amount by the tile ScrapSize (ISMoveableSpriteProps:addScrapItemToList:
-- Small halves it, at least 1; Large doubles it) and rolls each item with the skill chance: SIZE_FACTOR
-- undoes the size, so at full chance the material gives exactly the recipe outputs, and never more.

local Dismantle = require "LiveWater/LWT_Dismantle"

local GameScrap = {}

GameScrap.SIZE_FACTOR = { Small = 2, Medium = 1, Large = 0.5 }
-- Chance per roll; the skill chance (10 + 10 per level + baseChance) scales it.
GameScrap.CHANCE = 100

function GameScrap.declare(definitions, perks)
    for _, part in ipairs(Dismantle.PARTS) do
        local material = Dismantle.material(part)
        if material then
            local tool = Dismantle.TOOLS[part.tool]
            definitions.addScrapDefinition(material, tool.items, {}, perks[tool.perk], tool.scrapTime, tool.sound,
                true, tool.baseChance)
            for _, back in ipairs(part.returns) do
                definitions.addScrapItem(material, back[1], back[2] * GameScrap.SIZE_FACTOR[part.scrap],
                    GameScrap.CHANCE, true)
            end
        end
    end
end

Events.OnGameBoot.Add(function()
    GameScrap.declare(ISMoveableDefinitions:getInstance(), Perks)
end)

return GameScrap
