if isClient() then return end
-- LiveWater: where the water of an outlet goes, by outlet type (ADR-001 D13). A handler serves one
-- outlet type ("houseInlet": the relay tanks, LWT_Relays); a new kind of outlet registers its own
-- handler, the clock and the composition root never name a type. A handler is an object with
--   need(part)                     litres the outlet would take this step
--   deliver(part, litres, quality) the litres it was given (waterDelivered)
--   release(part)                  optional: the part left (pickup, removal)
-- No game API here; the part catalog is injected (outlet type = third result of the `outlet` hook).

local Outlets = {}
Outlets.__index = Outlets

function Outlets.new(catalog)
    return setmetatable({ catalog = catalog, handlers = {} }, Outlets)
end

-- Returns true, or false and "duplicate_outlet".
function Outlets:register(outletType, handler)
    if self.handlers[outletType] then return false, "duplicate_outlet" end
    self.handlers[outletType] = handler
    return true
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

return Outlets
