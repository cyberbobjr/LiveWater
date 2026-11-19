if isClient() then return end
-- LiveWater command "fitFilter" { x, y, z }: put a cartridge of the player's inventory into the
-- part (house water inlet, ADR-005). A cartridge already in comes out first (LWT_CmdCartridge.takeOut). The new
-- one keeps the wear its condition shows. Checks: those of LWT_CmdCartridge.find, then the
-- cartridge in the inventory (no_cartridge).

local Cartridge = require "LiveWater/Commands/LWT_CmdCartridge"

return function(ctx, player, args)
    local entry, item, fitted, left, spent = Cartridge.find(ctx, player, args)
    if not entry then return false, item end
    if not ctx.players:has(player, item) then return false, "no_cartridge" end
    local ok, share = ctx.players:take(player, item)
    if not ok then return false, "no_cartridge" end
    if fitted then Cartridge.takeOut(ctx, player, entry, item, left, spent) end
    ctx.catalog:call(entry, "fit", share or 1, ctx)
    ctx.publisher:present(entry)
    return true
end
