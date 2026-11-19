-- LiveWater: what dismantling each equipment takes and gives back (ADR-007 D01-D03). Pure data, the one
-- source of the inventory recipes LWTDismantle<name> (scripts/LWT_dismantle.txt, checked against this table
-- by tests/test_dismantle.py) and of the in-world scrap materials LiveWater<name> (LWT_GameScrap, tile
-- property Material of source/tiles/build_livewater_tiles.py).
--
-- A dismantle gives back at most what the build cost, in degraded materials (scrap metal, iron pieces,
-- screws, electronics scrap, wire, cloth): a part cut out of a quarter of a metal pipe or of a rubber hose
-- never gives a whole one back, so building then dismantling never gains material.

local Dismantle = {}

-- Prefix of the in-world scrap materials: material = MATERIAL_PREFIX .. part name.
Dismantle.MATERIAL_PREFIX = "LiveWater"
-- Prefix of the inventory recipes: recipe = RECIPE_PREFIX .. part name.
Dismantle.RECIPE_PREFIX = "LWTDismantle"

-- Tool kinds (D03).
--   tags         recipe tool tags (kept, any of them)
--   items        in-world scrap tools, any of them (ISMoveableDefinitions.addScrapDefinition)
--   perk         name in Perks of the skill that raises the in-world chance; nil: none
--   category, timedAction   of the recipe
--   scrapTime, sound, baseChance   of the in-world scrap definition
Dismantle.TOOLS = {
    plumbing = {
        tags = { "base:pipewrench", "base:wrench" },
        items = { "Base.PipeWrench", "Base.Wrench" },
        perk = "Maintenance",
        category = "LiveWater",
        timedAction = "Making",
        scrapTime = 300,
        sound = "RepairWithWrench",
        baseChance = 40,
    },
    electrical = {
        tags = { "base:screwdriver" },
        items = { "Base.Screwdriver" },
        perk = "Electricity",
        category = "LiveWater",
        timedAction = "DismantleElectrical",
        scrapTime = 500,
        sound = "Dismantle",
        baseChance = 20,
    },
    knife = {
        tags = { "base:sharpknife" },
        items = {},
        perk = nil,
        category = "LiveWater",
        timedAction = "Making",
    },
}

-- One entry per equipment.
--   name     part name (recipe and material suffix)
--   item     full type of the dismantled item
--   tool     key of TOOLS
--   time     recipe time
--   scrap    ScrapSize of its tiles when it is dismantled in the world too; nil: inventory only
--   returns  { { full type, amount } }, the recipe outputs and the in-world maximum
Dismantle.PARTS = {
    { name = "Pipe", item = "Base.Mov_LiveWater_Pipe", tool = "plumbing", time = 60, scrap = "Small",
      returns = { { "Base.IronPiece", 1 } } },
    { name = "Valve", item = "Base.Mov_LiveWater_Valve", tool = "plumbing", time = 100, scrap = "Small",
      returns = { { "Base.ScrapMetal", 1 }, { "Base.IronPiece", 1 } } },
    { name = "FlowMeter", item = "Base.Mov_LiveWater_FlowMeter", tool = "plumbing", time = 100, scrap = "Small",
      returns = { { "Base.IronPiece", 2 }, { "Base.Screws", 1 } } },
    { name = "HouseInlet", item = "Base.Mov_LiveWater_HouseInlet", tool = "plumbing", time = 150, scrap = "Medium",
      returns = { { "Base.ScrapMetal", 1 }, { "Base.IronPiece", 1 }, { "Base.Screws", 2 } } },
    { name = "PondPump", item = "Base.Mov_LiveWater_PondPump", tool = "electrical", time = 200, scrap = "Large",
      returns = { { "Base.ScrapMetal", 2 }, { "Base.Screws", 2 }, { "Base.ElectronicsScrap", 2 },
                  { "Base.ElectricWire", 1 } } },
    { name = "Sprinkler", item = "Base.Mov_LiveWater_Sprinkler", tool = "plumbing", time = 100, scrap = "Small",
      returns = { { "Base.ScrapMetal", 1 }, { "Base.IronPiece", 2 } } },
    { name = "SprinklerAuto", item = "Base.Mov_LiveWater_SprinklerAuto", tool = "electrical", time = 150,
      scrap = "Medium",
      returns = { { "Base.ScrapMetal", 1 }, { "Base.IronPiece", 2 }, { "Base.ElectronicsScrap", 1 },
                  { "Base.ElectricWire", 1 } } },
    { name = "BarrelFitting", item = "Base.Mov_LiveWater_BarrelFitting", tool = "plumbing", time = 80,
      scrap = "Small", returns = { { "Base.IronPiece", 1 } } },
    -- Picked up by hand and laid again: no in-world dismantle (D02).
    { name = "DripLine", item = "Base.Mov_LiveWater_DripLine", tool = "knife", time = 40,
      returns = { { "Base.RubberBand", 1 } } },
    -- Gives back cloth, never the burnt charcoal (D01).
    { name = "WaterFilter", item = "LiveWater.WaterFilter", tool = "knife", time = 40,
      returns = { { "Base.RippedSheets", 1 } } },
    { name = "WaterFilterSpent", item = "LiveWater.WaterFilterSpent", tool = "knife", time = 40,
      returns = { { "Base.RippedSheets", 1 } } },
}

function Dismantle.recipeName(part)
    return Dismantle.RECIPE_PREFIX .. part.name
end

-- In-world scrap material of a part, nil when it is dismantled in the inventory only.
function Dismantle.material(part)
    if part.scrap == nil then return nil end
    return Dismantle.MATERIAL_PREFIX .. part.name
end

return Dismantle
