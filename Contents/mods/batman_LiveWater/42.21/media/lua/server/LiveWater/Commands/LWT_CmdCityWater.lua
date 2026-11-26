if isClient() then return end
-- LiveWater command "cityWater" { x, y, z }: connect a fixture a player set down to the city water
-- (ADR-001 M01). Checks, on the authority: arguments, a fixture set down by a player and not
-- plumbed, or plumbed with no tank above (not_fixture), distance and floor, a room of a map building (not_map_building), the city
-- water still running on that square (no_city_water, LWT_CityWater); then the fixture takes the
-- state of an original one and the clients receive it (port ctx.plumbing, LWT_GamePlumbing).

local Checks = require "LiveWater/Commands/LWT_CmdChecks"
local CityWater = require "LiveWater/LWT_CityWater"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    local info = ctx.plumbing:cityFixture(x, y, z)
    if not CityWater.isFixture(info) then return false, "not_fixture" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    local refusal = CityWater.refusal(info, ctx.plumbing:cityWaterRuns())
    if refusal then return false, refusal end
    ctx.plumbing:connectCity(x, y, z)
    return true
end
