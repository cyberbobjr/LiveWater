if isClient() then return end
-- LiveWater: what the filter commands share (fitFilter, removeFilter; ADR-001 D17, Q02). A part
-- takes a removable cartridge when one of its capabilities answers the `cartridge` hook.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

local Cartridge = {}

-- Checks, in order: arguments, a part on the square, a cartridge slot, distance and floor.
-- Returns the entry, the cartridge item, fitted, share left; or nil and a reason.
function Cartridge.find(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return nil, "invalid" end
    local entry = ctx.topology:at(x, y, z)
    if not entry then return nil, "nothing_here" end
    local item, fitted, left = ctx.catalog:first(entry, "cartridge", ctx)
    if not item then return nil, "no_filter_slot" end
    if not Checks.near(ctx.players, player, x, y, z) then return nil, "too_far" end
    return entry, item, fitted, left
end

-- Take the fitted cartridge out: back to the player with the share left as its condition, or
-- thrown away when worn out.
function Cartridge.takeOut(ctx, player, entry, item, left)
    if left > 0 then ctx.players:give(player, item, left) end
    ctx.catalog:call(entry, "unfit")
end

return Cartridge
