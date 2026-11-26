-- LiveWater: connecting a fixture to the city water (ADR-001 D27, D28, M01). Pure rule shared by
-- the client menu and the server command. The engine gives a fixture the city's endless water
-- when it stands in a room of a map building, carries waterPiped, uses no outside source, its
-- square is not "no water", the shut-off day has not come, and its ModData has no
-- canBeWaterPiped = true (IsoObject.isWaterInfinite, Java 42.22): a fixture a player set down gets
-- canBeWaterPiped = true (ISMoveableSpriteProps), connecting it takes that mark away.
-- The game also offers its own "Plumb" on such a fixture before the shut-off, tank above or not
-- (ISWorldObjectContextMenuLogic, Java 42.22): plumbed with no tank above it stays dry, so it may
-- join the city water too.
-- info = { placed (canBeWaterPiped = true), plumbed (uses an outside source), source (a tank stands
-- above it), room (in a room of a map building), noWater (square marked without water) }, from
-- LWT_WaterObjects.cityInfo.

local CityWater = {}

-- A fixture a player set down and did not plumb, or plumbed with no tank above it.
function CityWater.isFixture(info)
    if info == nil then return false end
    if info.plumbed then return not info.source end
    return info.placed == true
end

-- nil when the fixture may join the city water now (`runs`: the city water still runs), else the
-- reason: "not_fixture", "not_map_building", "no_city_water".
function CityWater.refusal(info, runs)
    if not CityWater.isFixture(info) then return "not_fixture" end
    if not info.room then return "not_map_building" end
    if not runs or info.noWater then return "no_city_water" end
    return nil
end

return CityWater
