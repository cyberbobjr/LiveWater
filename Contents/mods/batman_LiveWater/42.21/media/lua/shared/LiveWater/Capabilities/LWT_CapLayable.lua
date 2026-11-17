-- LiveWater capability "layable": the part is not a moveable; it is laid on a square with one
-- inventory item and dismantled with a tool that gives the item back (ADR-001 Q01).
--   item  required full type of the item laid ("LiveWater.PipeSection")
--   tool  item tag of the tool needed to dismantle (default "base:pipewrench")

local Check = require "LiveWater/LWT_Check"

local function isFullType(v)
    return type(v) == "string" and #v <= 120 and string.match(v, "^%a[%w_]*%.%a[%w_]*$") ~= nil
end

local function isTag(v)
    return type(v) == "string" and #v <= 120 and string.match(v, "^%a[%w_]*:%a[%w_]*$") ~= nil
end

local SPEC = {
    item = { valid = isFullType },
    tool = { default = "base:pipewrench", valid = isTag },
}

local Layable = {}

function Layable.define(params)
    local out, field = Check.fields(params, SPEC)
    if out and out.item == nil then return nil, "item" end
    return out, field
end

function Layable.layable(p)
    return p.item, p.tool
end

return Layable
