-- LiveWater: sandbox settings seen by the capabilities (ADR-001 D07, ADR-006 D02). Pure: the
-- context of a step carries `scale(optionName)` (adapter LWT_GameSettings on the authority);
-- without it every multiplier is 1 and every value its fallback, the values of the part definitions.

local Settings = {}

-- Number of the sandbox option `name` (page LiveWater) in this context, or nil when absent or
-- not a number of 0 or more.
local function read(ctx, name)
    local fn = ctx and ctx.scale
    local v = fn and fn(name)
    if type(v) ~= "number" or v ~= v or v < 0 then return nil end
    return v
end

-- Multiplier of the sandbox option `name` in this context (1 when absent).
function Settings.scale(ctx, name)
    return read(ctx, name) or 1
end

-- Value of the sandbox option `name` in this context, or `fallback` when absent (ADR-006 D02:
-- litres of a flow).
function Settings.value(ctx, name, fallback)
    local v = read(ctx, name)
    if v == nil then return fallback end
    return v
end

-- Litres as text for the information lines: at most one decimal, no trailing ".0" (10, 7.5).
function Settings.litres(v)
    return (string.gsub(string.format("%.1f", v), "%.0$", ""))
end

return Settings
