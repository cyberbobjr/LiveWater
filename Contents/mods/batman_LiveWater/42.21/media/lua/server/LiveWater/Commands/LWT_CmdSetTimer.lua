if isClient() then return end
-- LiveWater command "setTimer" { x, y, z, hours }: hours between two openings of a sprinkler timer
-- (ADR-001 D19). Checks: arguments (hours a whole number), a part on the square, a timer (hook
-- `timer`), hours within the sandbox bounds SprinklerTimerMin and SprinklerTimerMax, distance.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"

local DEFAULT_MIN, DEFAULT_MAX = 1, 24

local function bound(ctx, name, default)
    local v = ctx.scale and ctx.scale(name)
    if type(v) ~= "number" or v ~= v or v < 1 then return default end
    return v
end

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    local hours = args.hours
    if not x or type(hours) ~= "number" or hours ~= hours or hours % 1 ~= 0 then return false, "invalid" end
    local entry = ctx.topology:at(x, y, z)
    if not entry then return false, "nothing_here" end
    if ctx.catalog:first(entry, "timer") == nil then return false, "not_timer" end
    if hours < bound(ctx, "SprinklerTimerMin", DEFAULT_MIN) or hours > bound(ctx, "SprinklerTimerMax", DEFAULT_MAX) then
        return false, "out_of_bounds"
    end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    ctx.catalog:call(entry, "setTimer", hours)
    ctx.publisher:present(entry)
    return true
end
