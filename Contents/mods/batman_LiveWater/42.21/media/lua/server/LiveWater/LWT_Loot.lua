if isClient() then return end
-- LiveWater: parts found as loot (ADR-007 D04). Each group adds its items, with a low weight (about a rare
-- tool of the same list), at the end of vanilla procedural lists when the tables merge; nothing is replaced
-- and a list that does not exist is skipped. The pond pump, the house inlet, the water meter and the
-- automatic sprinkler are never found: they stay crafted.

local Loot = {}

Loot.GROUPS = {
    -- Plumbing supplies and tool crates.
    {
        lists = { "PlumbingSupplies", "CrateTools", "GarageTools", "ToolStoreTools" },
        items = {
            { "Base.Mov_LiveWater_Pipe", 2 },
            { "Base.Mov_LiveWater_Valve", 1 },
            { "Base.Mov_LiveWater_BarrelFitting", 1 },
        },
    },
    -- Garden stores and farming supplies.
    {
        lists = { "GardenStoreTools", "GardenStoreMisc", "CrateGardening", "GigamartFarming", "ToolStoreFarming" },
        items = {
            { "Base.Mov_LiveWater_Sprinkler", 1 },
            { "Base.Mov_LiveWater_DripLine", 2 },
            { "LiveWater.WaterFilter", 1 },
        },
    },
}

-- Appends the groups to `lists` (ProceduralDistributions.list): item, weight pairs after the vanilla ones.
function Loot.apply(lists)
    for _, group in ipairs(Loot.GROUPS) do
        for _, name in ipairs(group.lists) do
            local list = lists[name]
            if list and list.items then
                for _, entry in ipairs(group.items) do
                    table.insert(list.items, entry[1])
                    table.insert(list.items, entry[2])
                end
            end
        end
    end
end

Events.OnPreDistributionMerge.Add(function()
    Loot.apply(ProceduralDistributions.list)
end)

return Loot
