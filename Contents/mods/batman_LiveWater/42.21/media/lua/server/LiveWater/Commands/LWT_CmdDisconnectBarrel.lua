if isClient() then return end
-- LiveWater command "disconnectBarrel" { x, y, z }: the barrel leaves the house reserve (ADR-001
-- D28). Checks: arguments, distance and floor, pipe wrench, a connected barrel there.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    if not ctx.players:hasTool(player, Checks.PIPE_WRENCH) then return false, "need_tool" end
    return ctx.barrels:disconnect(x, y, z)
end
