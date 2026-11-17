if isClient() then return end
-- LiveWater command "switchPump" { x, y, z }: turn the switch of the part over (pond pump, P03).
-- Checks: arguments, a part on the square, a switch (hook `switchable`), distance and floor.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    local entry = ctx.topology:at(x, y, z)
    if not entry then return false, "nothing_here" end
    local on = ctx.catalog:first(entry, "switchable")
    if on == nil then return false, "not_switchable" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    ctx.catalog:call(entry, "switch", not on)
    ctx.publisher:present(entry)
    return true
end
