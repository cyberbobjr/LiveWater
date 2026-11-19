if isClient() then return end
-- LiveWater: where the water of an outlet goes, by outlet type (ADR-001 D13). A handler serves one
-- outlet type ("houseInlet": the relay tanks, LWT_Relays); a new kind of outlet registers its own
-- handler, the clock never names a type. A handler follows the contract of LWT_OutletTypes (need,
-- deliver, optional release and cut); LiveWater's own are registered by the composition root, the
-- other mods' (LiveWater.API.registerOutlet, ADR-012 D04) are adopted from LiveWater.OutletTypes.
-- No game API here; the part catalog is injected (outlet type = third result of the `outlet` hook).

local OutletTypes = require "LiveWater/LWT_OutletTypes"

local Outlets = {}
Outlets.__index = Outlets

function Outlets.new(catalog)
    return setmetatable({ catalog = catalog, handlers = {} }, Outlets)
end

-- Returns true, or false and "invalid_type", "invalid_handler", "duplicate_outlet".
function Outlets:register(outletType, handler)
    if not OutletTypes.isType(outletType) then return false, "invalid_type" end
    if not OutletTypes.check(handler) then return false, "invalid_handler" end
    if self.handlers[outletType] then return false, "duplicate_outlet" end
    self.handlers[outletType] = handler
    return true
end

-- Every handler registered through the API (LWT_OutletTypes). Returns how many were added.
function Outlets:adopt(types)
    local list, handlers = types:all()
    local count = 0
    for i = 1, #list do
        if self:register(list[i], handlers[list[i]]) then count = count + 1 end
    end
    return count
end

function Outlets:handlerOf(part)
    local _, _, outletType = self.catalog:first(part, "outlet")
    return outletType and self.handlers[outletType] or nil
end

function Outlets:need(part)
    local handler = self:handlerOf(part)
    return handler and handler:need(part) or 0
end

function Outlets:deliver(part, litres, quality)
    local handler = self:handlerOf(part)
    if handler then handler:deliver(part, litres, quality) end
end

function Outlets:release(part)
    local handler = self:handlerOf(part)
    if handler and handler.release then handler:release(part) end
end

function Outlets:cut(part)
    local handler = self:handlerOf(part)
    if handler and handler.cut then handler:cut(part) end
end

return Outlets
