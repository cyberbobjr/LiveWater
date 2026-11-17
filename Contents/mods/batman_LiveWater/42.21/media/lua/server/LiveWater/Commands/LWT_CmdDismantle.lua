if isClient() then return end
-- LiveWater command "dismantle" { x, y, z }: take up a part that was laid with an item
-- (capability "layable") and give the item back, with the tool the part names (pipe wrench for
-- a pipe, ADR-001 Q01). Checks: arguments, a part on the square, laid with an item, distance
-- and floor, tool in the inventory.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    local entry = ctx.topology:at(x, y, z)
    if not entry then return false, "nothing_here" end
    local item, tool = ctx.catalog:first(entry, "layable")
    if not item then return false, "not_layable" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    if not ctx.players:hasTool(player, tool) then return false, "need_tool" end
    ctx.topology:remove(x, y, z)
    ctx.world:removePart(x, y, z, entry.type)
    ctx.players:give(player, item)
    return true
end
