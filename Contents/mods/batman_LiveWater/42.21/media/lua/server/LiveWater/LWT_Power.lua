if isClient() then return end
-- LiveWater: the only adapter of electric current (ADR-001 D20), on the authority.
--   register(liveWireApi)  at OnInitWorld (every mod's Lua is loaded, Live Wire not sealed yet):
--                          when Live Wire's API has revision 6 or later, every part type that
--                          needs current (`power` hook true for a new part: pump, sprinkler
--                          timer) becomes a Live Wire consumer (LWT_LiveWireConsumers, the base
--                          definition a multiplayer client registers too, ADR-017 D03): with
--                          revision 9 or later, a type whose definition carries `link` (the pump,
--                          Electrical 2) may be wired to an inverter (ADR-017 D01). This side adds:
--                          billed `watts` while running, 0 when stopped, `display` (its information
--                          lines, at most 4) and `summary` (pumps running, water pumped), in the
--                          format of Live Wire ADR-002. Returns how many types were registered.
--   powered(part)          current this step. On a loaded square: Live Wire's consumerPowered for a
--                          registered type (it follows the wire of a linked part, else the power
--                          of the square; circuits and breakers included), else the vanilla rule
--                          of the square (a generator in range or the public grid); what was read
--                          is recorded in the part state (STATE_KEY) for the absence. On a square
--                          not loaded (ADR-006 D07): a part of a linkable type wired to an inverter
--                          (Live Wire's consumerLinkPowered answers a boolean, registry only)
--                          has current when that inverter supplies it and the last loaded
--                          consumerPowered allowed it (ADR-017 D02); else, with Live Wire's gridAt
--                          (authority, reads its registry only), the inverter of the grid that
--                          covers the square is on and the last loaded consumerPowered allowed it
--                          (circuit, breaker); when no Live Wire grid covers it: the public grid if
--                          it still runs in the world (global state) and the square had it when
--                          last loaded, or a generator in range at the last loaded step (the
--                          generator itself is neither read nor touched).
-- Live Wire is never required (no require=) and never modified (D21). Dependencies: { catalog,
-- world (port: isLoaded, object, powerAt -> generator, grid (nil when not loaded), gridRuns,
-- stateOfObject) }.

local Consumers = require "LiveWater/LWT_LiveWireConsumers"

local Power = {}
Power.__index = Power

Power.MAX_DISPLAY_LINES = 4
-- Key of the record of the last loaded reading in the part state: not a capability kind (a kind
-- starts with a letter, LWT_Check.isName), kept by the registry with the rest of the state.
Power.STATE_KEY = "_power"

function Power.new(deps)
    return setmetatable({ catalog = deps.catalog, world = deps.world, api = nil, registered = {} }, Power)
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

-- What the authority adds to the shared consumer definition: draw, information, summary.
function Power:complete(def)
    def.powerConsumption = function(o) return self:watts(o) end
    def.display = function(o) return self:display(o) end
    def.summary = function(objects) return self:summary(objects) end
end

function Power:register(api)
    self.api, self.registered = nil, {}
    local count, registered = Consumers.register(api, self.catalog, function(_, def) self:complete(def) end)
    if Consumers.usable(api) then self.api, self.registered = api, registered end
    return count
end

-- Last loaded reading of a part: { generator, grid, live (nil: not a Live Wire consumer) } or nil.
local function recordOf(part)
    return part.data and part.data[Power.STATE_KEY] or nil
end

-- Reading of a part on a loaded square, recorded for the absence.
function Power:readLoaded(part)
    local x, y, z = part.x, part.y, part.z
    local generator, grid = self.world:powerAt(x, y, z)
    local record = { generator = generator == true, grid = grid == true }
    local on = record.generator or record.grid
    if self.registered[part.type] then
        local obj = self.world:object(x, y, z, part.type)
        record.live = obj ~= nil and self.api.consumerPowered(obj) == true
        on = record.live
    end
    part.data = part.data or {}
    part.data[Power.STATE_KEY] = record
    return on
end

-- Snapshot of the Live Wire grid that covers the square of a registered part, or nil.
function Power:liveGrid(part)
    if not self.registered[part.type] or type(self.api.gridAt) ~= "function" then return nil end
    local snapshot = self.api.gridAt(part.x, part.y, part.z)
    if type(snapshot) ~= "table" or type(snapshot.inverter) ~= "table" then return nil end
    return snapshot
end

-- Is the linkable registered part wired to a supplied inverter? true, false, or nil when it is not
-- wired (or Live Wire cannot tell: no consumerLinkPowered before revision 9).
function Power:linkSupplied(part)
    local def = self.registered[part.type]
    if not def or not def.link or type(self.api.consumerLinkPowered) ~= "function" then return nil end
    local supplied = self.api.consumerLinkPowered(part.x, part.y, part.z)
    if type(supplied) ~= "boolean" then return nil end
    return supplied
end

-- Current of a part whose square is not loaded (ADR-006 D07, ADR-017 D02).
function Power:readAway(part)
    local record = recordOf(part) or {}
    local linked = self:linkSupplied(part)
    if linked ~= nil then return linked and record.live ~= false end
    local snapshot = self:liveGrid(part)
    if snapshot then return snapshot.inverter.powered == true and record.live ~= false end
    if record.generator then return true end
    return record.grid ~= false and self.world:gridRuns() == true
end

function Power:powered(part)
    if self.world:isLoaded(part.x, part.y, part.z) then return self:readLoaded(part) end
    return self:readAway(part)
end

return Power
