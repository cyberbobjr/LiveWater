if isClient() then return end
-- LiveWater command "switchValve" { x, y, z }: open or close the valve of the part (sprinkler, D19).
-- Checks: arguments, a part on the square, a valve (hook `opened`), distance and floor. Announces
-- valveChanged (part, open) (D06).

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    local entry = ctx.topology:at(x, y, z)
    if not entry then return false, "nothing_here" end
    local open = ctx.catalog:first(entry, "opened")
    if open == nil then return false, "not_valve" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    ctx.catalog:call(entry, "open", not open)
    ctx.publisher:present(entry)
    ctx.events.emit("valveChanged", entry, not open)
    return true
end
