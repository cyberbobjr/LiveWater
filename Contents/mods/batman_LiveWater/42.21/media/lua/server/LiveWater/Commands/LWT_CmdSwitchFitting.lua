if isClient() then return end
-- LiveWater command "switchFitting" { x, y, z }: a barrel fitting goes from Fill to Pump or back
-- (ADR-001 D26). Checks: arguments, a part on the square, a fitting (hook `fittingMode`), distance.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

local NEXT = { fill = "pump", pump = "fill" }

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    local entry = ctx.topology:at(x, y, z)
    if not entry then return false, "nothing_here" end
    local mode = ctx.catalog:first(entry, "fittingMode")
    if not mode then return false, "not_fitting" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    ctx.catalog:call(entry, "setFittingMode", NEXT[mode])
    ctx.publisher:present(entry)
    return true
end
