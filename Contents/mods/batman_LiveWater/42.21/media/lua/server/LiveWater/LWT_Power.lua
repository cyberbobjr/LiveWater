if isClient() then return end
-- LiveWater: the only adapter of electric current (ADR-001 D20), on the authority.
--   register(liveWireApi)  at OnInitWorld (every mod's Lua is loaded, Live Wire not sealed yet):
--                          when Live Wire's API has revision 6 or later, every part type that
--                          needs current (`power` hook true for a new part: pump, sprinkler
--                          timer) becomes a Live Wire consumer: billed
--                          `watts` while running, 0 when stopped, `display` (its information
--                          lines, at most 4) and `summary` (pumps running, water pumped), in the
--                          format of Live Wire ADR-002. Returns how many types were registered.
--   powered(part)          current this step: Live Wire's consumerPowered for a registered type
--                          (circuits and breakers included), else the vanilla rule of the square.
-- Live Wire is never required (no require=) and never modified (D21). Dependencies: { catalog,
-- world (port: object, hasPower, stateOfObject) }.

local Power = {}
Power.__index = Power

Power.MIN_REVISION = 6
Power.MAX_DISPLAY_LINES = 4

function Power.new(deps)
    return setmetatable({ catalog = deps.catalog, world = deps.world, api = nil, registered = {} }, Power)
end

-- Live Wire consumer id of a part type ("LiveWater:PondPump" -> "LiveWater_LiveWater_PondPump").
function Power.consumerId(typeId)
    return "LiveWater_" .. string.gsub(typeId, ":", "_")
end

-- The part a game object stands for, from its mirrored state: { type, data }, or nil.
function Power:partOf(obj)
    local state = self.world:stateOfObject(obj)
    if not state or not self.catalog:has(state.type) then return nil end
    return { type = state.type, data = state.data or {} }
end

function Power:watts(obj)
    local part = self:partOf(obj)
    if not part then return 0 end
    local _, watts = self.catalog:first(part, "power")
    return watts or 0
end

function Power:display(obj)
    local part = self:partOf(obj)
    if not part then return nil end
    local lines, out = self.catalog:lines(part), {}
    for i = 1, math.min(#lines, Power.MAX_DISPLAY_LINES) do out[i] = lines[i] end
    if #out == 0 then return nil end
    return { lines = out }
end

-- Pumps running among the objects served by a Live Wire network, and the water they pumped.
-- Only the parts that pressurize count as pumps (a sprinkler timer is a consumer too).
function Power:summary(objects)
    local pumps, running, litres = 0, 0, 0
    for i = 1, #objects do
        local part = self:partOf(objects[i])
        if part and self.catalog:any(part, "pressurizes") then
            pumps = pumps + 1
            local _, watts = self.catalog:first(part, "power")
            if watts and watts > 0 then running = running + 1 end
            litres = litres + (self.catalog:first(part, "output") or 0)
        end
    end
    return { lines = {
        { "IGUI_LWT_LW_Pumps", running, pumps },
        { "IGUI_LWT_LW_Flow", math.floor(litres + 0.5) },
    } }
end

function Power:definition(typeId)
    return {
        sprites = self.catalog:spritesOf(typeId),
        powerConsumption = function(o) return self:watts(o) end,
        category = "other",
        circuit = "equipment",
        display = function(o) return self:display(o) end,
        summary = function(objects) return self:summary(objects) end,
    }
end

function Power:register(api)
    self.api, self.registered = nil, {}
    if type(api) ~= "table" or type(api.revision) ~= "number" or api.revision < Power.MIN_REVISION
        or type(api.registerConsumer) ~= "function" then
        return 0
    end
    self.api = api
    local count, ids = 0, self.catalog:ids()
    for i = 1, #ids do
        local id = ids[i]
        if self.catalog:first({ type = id }, "power") then
            local ok, reason = api.registerConsumer(Power.consumerId(id), self:definition(id))
            if ok or reason == "duplicate_consumer" then
                self.registered[id] = true
                count = count + 1
            else
                print("LiveWater: Live Wire consumer " .. id .. " not registered: " .. tostring(reason))
            end
        end
    end
    return count
end

function Power:powered(part)
    if self.registered[part.type] then
        local obj = self.world:object(part.x, part.y, part.z, part.type)
        return obj ~= nil and self.api.consumerPowered(obj) == true
    end
    return self.world:hasPower(part.x, part.y, part.z) == true
end

return Power
