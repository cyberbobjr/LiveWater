if isClient() then return end
-- LiveWater: what players see of a part's state, on the authority (ADR-001 D11). After a step or
-- an action, present(part):
--   the sprite follows the state (LWT_Sprites:show: variants, facing kept);
--   the state is mirrored on the game object ({ type, data }, LWT_Mirror) only when it changed,
--   for the client menus, Live Wire and a moveable picked up then set down again;
--   its sound loop (`sound` hook: pump P15, sprinkler P14) starts or stops for the players when it changes; after a
--   step (present(part, true)) a part that makes noise is heard by zombies and its loop is told
--   again (players who came near since).
--   a part with a jet (`jet` hook, sprinkler, D08a) tells the clients when it starts or stops
--   spraying, after its state is mirrored: they read it again and animate the jet.
-- No game API here; dependencies are injected: { catalog, sprites (LWT_Sprites), mirror (port:
-- writeState(x, y, z, typeId, state)), sounds (optional port: loop(x, y, z, name or nil),
-- noise(x, y, z, radius, volume)), visuals (optional port: jet(x, y, z)) }.

local Grid = require "LiveWater/LWT_Grid"

local Publisher = {}
Publisher.__index = Publisher

function Publisher.new(deps)
    return setmetatable({ catalog = deps.catalog, sprites = deps.sprites, mirror = deps.mirror, sounds = deps.sounds,
        visuals = deps.visuals, sent = {}, playing = {}, spraying = {} }, Publisher)
end

-- Text of a value with sorted keys: two equal states give the same text.
function Publisher.signature(v)
    if type(v) ~= "table" then return tostring(v) end
    local keys = {}
    for k in pairs(v) do keys[#keys + 1] = tostring(k) end
    table.sort(keys)
    local out = {}
    for i = 1, #keys do
        local k = keys[i]
        local value = v[k]
        if value == nil then value = v[tonumber(k)] end
        out[i] = k .. "=" .. Publisher.signature(value)
    end
    return "{" .. table.concat(out, ",") .. "}"
end

local function isEmpty(t)
    for _ in pairs(t) do return false end
    return true
end

-- Sound loop and noise of the part; `stepped`: after a ten-minute step.
function Publisher:sound(part, key, stepped)
    if not self.sounds then return end
    local name, radius, volume = self.catalog:first(part, "sound")
    if name then
        if stepped then self.sounds:noise(part.x, part.y, part.z, radius, volume) end
        if stepped or self.playing[key] ~= name then
            self.sounds:loop(part.x, part.y, part.z, name)
            self.playing[key] = name
        end
    elseif self.playing[key] then
        self.sounds:loop(part.x, part.y, part.z, nil)
        self.playing[key] = nil
    end
end

-- The jet of the part started or stopped: the clients are told (after the mirror).
function Publisher:jet(part, key)
    if not self.visuals then return end
    local sheet, _, _, on = self.catalog:first(part, "jet")
    on = sheet ~= nil and on == true
    if (self.spraying[key] == true) ~= on then
        self.spraying[key] = on or nil
        self.visuals:jet(part.x, part.y, part.z)
    end
end

-- A part without state (a pipe) is never mirrored.
function Publisher:present(part, stepped)
    local x, y, z = part.x, part.y, part.z
    self.sprites:show(x, y, z)
    local key = Grid.key(x, y, z)
    self:sound(part, key, stepped)
    local data = part.data or {}
    if self.sent[key] == nil and isEmpty(data) then return end
    local state = { type = part.type, data = data }
    local sig = Publisher.signature(state)
    if self.sent[key] ~= sig and self.mirror:writeState(x, y, z, part.type, state) then
        self.sent[key] = sig
    end
    self:jet(part, key)
end

-- The part left its square: the next one there is presented anew.
function Publisher:forget(part)
    local key = Grid.key(part.x, part.y, part.z)
    self.sent[key] = nil
    if self.playing[key] then
        self.sounds:loop(part.x, part.y, part.z, nil)
        self.playing[key] = nil
    end
    if self.spraying[key] then
        self.spraying[key] = nil
        self.visuals:jet(part.x, part.y, part.z)
    end
end

return Publisher
