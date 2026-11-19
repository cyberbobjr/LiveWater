if isClient() then return end
-- LiveWater command "removeFilter" { x, y, z }: take the cartridge out of the part; it comes back
-- with the share left as its condition, or as the spent item when worn out. Checks: those of
-- LWT_CmdCartridge.find, then a cartridge fitted (no_filter).

local Cartridge = require "LiveWater/Commands/LWT_CmdCartridge"

return function(ctx, player, args)
    local entry, item, fitted, left, spent = Cartridge.find(ctx, player, args)
    if not entry then return false, item end
    if not fitted then return false, "no_filter" end
    Cartridge.takeOut(ctx, player, entry, item, left, spent)
    ctx.publisher:present(entry)
    return true
end
