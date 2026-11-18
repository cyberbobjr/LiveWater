if isClient() then return end
-- LiveWater command "showNetwork" { x, y, z }: the squares of the network of the part there go back to
-- the player (reply "network" { parts = { { x, y, z } } }), who highlights them (LWT_NetworkView, D11).
-- Checks: arguments, a part on the square, distance. At most MAX_PARTS squares.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"
local Protocol = require "LiveWater/LWT_Protocol"

local MAX_PARTS = 500

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    if not ctx.topology:at(x, y, z) then return false, "nothing_here" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    local members, parts = ctx.topology:networkOf(x, y, z), {}
    for i = 1, math.min(#members, MAX_PARTS) do
        parts[i] = { x = members[i].x, y = members[i].y, z = members[i].z }
    end
    ctx.replies:to(player, Protocol.NETWORK, { parts = parts })
    return true
end
