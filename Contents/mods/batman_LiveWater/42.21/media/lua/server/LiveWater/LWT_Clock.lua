if isClient() then return end
-- LiveWater: the ten-minute step of every working network (ADR-001 D06, D09, D20). The composition
-- root subscribes tick() to Events.EveryTenMinutes, once, on the authority. Work is bounded: a
-- network is stepped only when one of its pressurizing parts stands on a loaded square. A step:
--   1. every member that needs current is told whether it has some (power port, `powered` hook);
--   2. the distribution (LWT_Flow);
--   3. every member hears the outcome (`stepped` hook: litres through it), then is presented
--      (sprite by state, mirrored state: publisher port);
--   4. each outlet served announces waterDelivered (part, litres, quality).
-- No game API here; dependencies are injected: { network, flow, catalog, world (port with
-- isLoaded(x, y, z)), events, need = function(part) -> litres (default 0), power (optional
-- port: powered(part) -> bool), publisher (optional port: present(part)), scale (optional:
-- function(optionName) -> sandbox multiplier) }.

local Grid = require "LiveWater/LWT_Grid"

local Clock = {}
Clock.__index = Clock

local function noNeed()
    return 0
end

function Clock.new(deps)
    return setmetatable({
        network = deps.network, flow = deps.flow, catalog = deps.catalog, world = deps.world,
        events = deps.events, power = deps.power, publisher = deps.publisher,
        ctx = { need = deps.need or noNeed, scale = deps.scale },
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

-- Tell the members that need current whether they have some.
function Clock:checkPower(members)
    if not self.power then return end
    for i = 1, #members do
        local part = members[i]
        if self.catalog:first(part, "power") then
            self.catalog:call(part, "powered", self.power:powered(part))
        end
    end
end

-- Every member hears the outcome of the step and is presented.
function Clock:conclude(members, result)
    for i = 1, #members do
        local part = members[i]
        local key = Grid.key(part.x, part.y, part.z)
        self.catalog:call(part, "stepped", { through = result.through[key] or 0, quality = result.quality }, self.ctx)
        if self.publisher then self.publisher:present(part) end
    end
end

-- One step of every awake network. Returns the list of the network ids stepped.
function Clock:tick()
    local stepped, ids = {}, self.network:ids()
    for i = 1, #ids do
        local id = ids[i]
        if self:isAwake(id) then
            local members = self.network:members(id)
            self:checkPower(members)
            local result = self.flow:step(self.network, id, self.ctx)
            self:conclude(members, result)
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
