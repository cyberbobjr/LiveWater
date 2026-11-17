-- LiveWater: sandbox multipliers seen by the capabilities (ADR-001 D07). Pure: the context of a
-- step carries `scale(optionName)` (adapter LWT_GameSettings on the authority); without it every
-- multiplier is 1, the values of the part definitions.

local Settings = {}

-- Multiplier of the sandbox option `name` (page LiveWater) in this context.
function Settings.scale(ctx, name)
    local fn = ctx and ctx.scale
    local v = fn and fn(name)
    if type(v) ~= "number" or v ~= v or v < 0 then return 1 end
    return v
end

return Settings
