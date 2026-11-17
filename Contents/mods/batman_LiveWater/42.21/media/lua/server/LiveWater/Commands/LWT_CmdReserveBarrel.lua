if isClient() then return end
-- LiveWater command "reserveBarrel" { x, y, z }: keep a connected barrel in reserve (taken last),
-- or take from it again with the others (ADR-001 D28, L06). Checks: arguments, distance and floor,
-- a connected barrel there.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    return ctx.barrels:toggleReserve(x, y, z)
end
