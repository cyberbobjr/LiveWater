if isClient() then return end
-- LiveWater command "lay" { x, y, z, part }: lay a part that is laid with an item (capability
-- "layable", e.g. a pipe and its LiveWater.PipeSection, ADR-001 Q01) on a free square near the
-- player. Checks, in order: arguments, part laid with an item, distance and floor, square
-- loaded and free, topology (occupied, ports), item in the inventory. Then the item is taken,
-- the tile created and the part joins the topology (sprites follow).

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x or type(args.part) ~= "string" then return false, "invalid" end
    local partType = args.part
    local item = ctx.catalog:first({ type = partType }, "layable")
    if not item then return false, "not_layable" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    if not ctx.world:isLoaded(x, y, z) then return false, "not_loaded" end
    if not ctx.world:isFree(x, y, z) then return false, "blocked" end
    local ok, reason = ctx.topology:canAdd(partType, x, y, z)
    if not ok then return false, reason end
    if not ctx.players:has(player, item) or not ctx.players:take(player, item) then return false, "no_item" end
    ctx.world:createPart(x, y, z, ctx.catalog:sprite(partType, 0))
    return ctx.topology:add(partType, x, y, z)
end
