if isClient() then return end
-- LiveWater command "repairPump" { x, y, z }: repair a stopped, worn or broken part with the
-- material it names (pond pump: 2 scrap metal and a wrench, P05). Checks, in order: arguments,
-- a part on the square, a repair (hook `repairable`), not running, worn or broken, distance and
-- floor, tool, material count. The material is used up.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    local entry = ctx.topology:at(x, y, z)
    if not entry then return false, "nothing_here" end
    local item, count, tool, why = ctx.catalog:first(entry, "repairable")
    if not item then return false, "not_repairable" end
    if why then return false, why end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    if tool and not ctx.players:hasTool(player, tool) then return false, "need_wrench" end
    if ctx.players:count(player, item) < count then return false, "no_parts" end
    for _ = 1, count do ctx.players:take(player, item) end
    ctx.catalog:call(entry, "repair")
    ctx.publisher:present(entry)
    return true
end
