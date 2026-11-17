-- LiveWater: public event bus (ADR-001 D06). Another mod reacts to LiveWater without wrapping
-- any of its functions:
--   LiveWater.Events.on("waterDelivered", function(part, litres, quality) ... end)
-- Events, emitted on the authority only:
--   partAdded (part)  partRemoved (part)  networkChanged (networkId)
--   waterDelivered (part, litres, quality)  valveChanged (part, open)
-- Subscribers run in subscription order; the same function subscribed twice runs once; emit
-- does not catch errors. This is not the engine's Events table.

local EventBus = {}

EventBus.NAMES = { "partAdded", "partRemoved", "networkChanged", "waterDelivered", "valveChanged" }

-- New bus for the given list of event names. on/off return true, or false and
-- "unknown_event" or "invalid_handler"; emit of an unknown name is a programming error.
function EventBus.new(names)
    local known, listeners, bus = {}, {}, {}
    for i = 1, #names do
        known[names[i]] = true
        listeners[names[i]] = {}
    end

    function bus.on(name, fn)
        if not known[name] then return false, "unknown_event" end
        if type(fn) ~= "function" then return false, "invalid_handler" end
        local list = listeners[name]
        for i = 1, #list do
            if list[i] == fn then return true end
        end
        list[#list + 1] = fn
        return true
    end

    function bus.off(name, fn)
        if not known[name] then return false, "unknown_event" end
        local list = listeners[name]
        for i = 1, #list do
            if list[i] == fn then
                table.remove(list, i)
                return true
            end
        end
        return true
    end

    function bus.emit(name, ...)
        if not known[name] then error("LiveWater.Events: unknown event " .. tostring(name), 2) end
        local list, snapshot = listeners[name], {}
        for i = 1, #list do snapshot[i] = list[i] end
        for i = 1, #snapshot do snapshot[i](...) end
    end

    return bus
end

return EventBus
