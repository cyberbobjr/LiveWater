if isClient() then return end
-- LiveWater: the ten-minute step of every working network (ADR-001 D06, D09). The composition
-- root subscribes tick() to Events.EveryTenMinutes, once, on the authority. Work is bounded: a
-- network is stepped only when one of its pressurizing parts stands on a loaded square; each
-- outlet served announces waterDelivered (part, litres, quality).
-- No game API here; dependencies are injected: { network, flow, catalog, world (port with
-- isLoaded(x, y, z)), events, need = function(part) -> litres (default 0) }.

local Clock = {}
Clock.__index = Clock

local function noNeed()
    return 0
end

function Clock.new(deps)
    return setmetatable({
        network = deps.network, flow = deps.flow, catalog = deps.catalog, world = deps.world,
        events = deps.events, ctx = { need = deps.need or noNeed },
    }, Clock)
end

-- Is a pressurizing part of network `id` on a loaded square?
function Clock:isAwake(id)
    local members = self.network:members(id)
    for i = 1, #members do
        local part = members[i]
        if self.catalog:any(part, "pressurizes") and self.world:isLoaded(part.x, part.y, part.z) then
            return true
        end
    end
    return false
end

-- One step of every awake network. Returns the list of the network ids stepped.
function Clock:tick()
    local stepped, ids = {}, self.network:ids()
    for i = 1, #ids do
        local id = ids[i]
        if self:isAwake(id) then
            local result = self.flow:step(self.network, id, self.ctx)
            stepped[#stepped + 1] = id
            for j = 1, #result.outlets do
                local out = result.outlets[j]
                if out.state == "served" then
                    self.events.emit("waterDelivered", out.part, out.litres, out.quality)
                end
            end
        end
    end
    return stepped
end

return Clock
