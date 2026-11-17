if isClient() then return end
-- LiveWater command "connectBarrel" { x, y, z }: connect a barrel or rain collector to the house
-- inlet of its building (ADR-001 D28, L01). Checks: arguments, distance and floor, pipe wrench,
-- then the barrel service (a barrel there, an inlet whose building holds it or its roof).

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    if not ctx.players:hasTool(player, Checks.PIPE_WRENCH) then return false, "need_tool" end
    return ctx.barrels:connect(x, y, z)
end
