if isClient() then return end
-- LiveWater command "unplumb" { x, y, z }: take the plumbing of a fixture away (ADR-024 D04).
-- Checks, on the authority: arguments, a plumbed fixture on the square (not_plumbed, LWT_Plumbing),
-- distance and floor, a pipe wrench as the client menu asks it (need_tool, LWT_Wrench); then the
-- fixture goes back to "set down, to plumb" and the clients receive it (port ctx.plumbing,
-- LWT_GamePlumbing).

local Checks = require "LiveWater/Commands/LWT_CmdChecks"
local Plumbing = require "LiveWater/LWT_Plumbing"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    local refusal = Plumbing.unplumbRefusal(ctx.plumbing:plumbInfo(x, y, z))
    if refusal then return false, refusal end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    if not ctx.players:hasWrench(player) then return false, "need_tool" end
    ctx.plumbing:unplumb(x, y, z)
    return true
end
