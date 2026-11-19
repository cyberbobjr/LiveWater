-- LiveWater capability "filter": makes water clean and wears by volume (ADR-001 D17, Q02).
--   capacity  litres one cartridge filters (default 500), times the sandbox option
--             FilterCapacityMultiplier
--   item      optional full type of a removable cartridge ("LiveWater.WaterFilter"): the part
--             filters only while one is fitted; without it the filter is built in
--   spent     optional full type of that cartridge once worn out ("LiveWater.WaterFilterSpent",
--             ADR-009 D01): taken out worn, it comes back as this item; without it, it is thrown away
-- State: { used = litres filtered by the current cartridge, fitted = a cartridge is in,
--          capacity = litres of the fitted cartridge, rated when it went in }.

local Check = require "LiveWater/LWT_Check"
local Settings = require "LiveWater/LWT_Settings"

local function isFullType(v)
    return type(v) == "string" and #v <= 120 and string.match(v, "^%a[%w_]*%.%a[%w_]*$") ~= nil
end

local SPEC = {
    capacity = Check.number(1, 1000000, 500),
    item = { valid = isFullType },
    spent = { valid = isFullType },
}

local Filter = {}

function Filter.define(params)
    return Check.fields(params, SPEC)
end

local function capacity(p, d, ctx)
    if d and d.capacity then return d.capacity end
    return p.capacity * Settings.scale(ctx, "FilterCapacityMultiplier")
end

local function fitted(p, d)
    return p.item == nil or (d ~= nil and d.fitted == true)
end

-- Share of the cartridge left, 0..1.
local function left(p, d, ctx)
    return math.max(0, 1 - (d and d.used or 0) / capacity(p, d, ctx))
end

function Filter.purifies(p, d, ctx)
    return fitted(p, d) and (d and d.used or 0) < capacity(p, d, ctx)
end

function Filter.wear(p, d, litres, ctx)
    d.used = math.min(capacity(p, d, ctx), (d.used or 0) + litres)
end

-- Removable cartridge: its item, whether one is fitted, the share of it left and the item it
-- becomes once worn out (nil: none); nil when the filter is built in.
function Filter.cartridge(p, d, ctx)
    if p.item == nil then return nil end
    return p.item, fitted(p, d), fitted(p, d) and left(p, d, ctx) or 0, p.spent
end

-- A cartridge with `share` (0..1) left goes in.
function Filter.fit(p, d, share, ctx)
    d.fitted = true
    d.capacity = p.capacity * Settings.scale(ctx, "FilterCapacityMultiplier")
    d.used = d.capacity * (1 - math.max(0, math.min(1, share or 1)))
end

function Filter.unfit(p, d)
    d.fitted = false
    d.used = 0
    d.capacity = nil
end

function Filter.look(p, d)
    if p.item ~= nil and fitted(p, d) then return "filter" end
    return nil
end

function Filter.lines(p, d)
    if not fitted(p, d) then return { { "IGUI_LWT_Filter_None", rank = 30 } } end
    if not Filter.purifies(p, d) then return { { "IGUI_LWT_Filter_Worn", rank = 30 } } end
    return { { "IGUI_LWT_Filter_Left", math.floor(left(p, d) * 100 + 0.5), rank = 30 } }
end

-- Actions of the part menu: { command, key, item = item the player must carry }.
function Filter.actions(p, d)
    if p.item == nil then return {} end
    local list = {}
    if fitted(p, d) then
        list[#list + 1] = { command = "removeFilter", key = "ContextMenu_LWT_RemoveFilter" }
        list[#list + 1] = { command = "fitFilter", key = "ContextMenu_LWT_ReplaceFilter", item = p.item }
    else
        list[#list + 1] = { command = "fitFilter", key = "ContextMenu_LWT_FitFilter", item = p.item }
    end
    return list
end

return Filter
