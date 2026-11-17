-- LiveWater: registry of part types (ADR-001 D01-D03, D05, D12). Pure, no game API; the
-- capability registry is injected. A definition is copied by whitelist:
--   sprites       required: { [mask] = spriteName } for masks 0..15 (side mask of LWT_Grid);
--                 a sprite belongs to one part type only
--   sides         optional: mask of the sides the part may connect by (default 15)
--   capabilities  required: { kind = params or true }, every kind registered, params checked
--                 by the kind's define hook
-- Placed parts carry their type in `part.type`; this registry is also the catalog the domain
-- modules (network, flow) ask about a part, without knowing any kind by name.

local Check = require "LiveWater/LWT_Check"
local Grid = require "LiveWater/LWT_Grid"

local Parts = {}
Parts.__index = Parts

function Parts.new(capabilities)
    return setmetatable({ capabilities = capabilities, defs = {}, bySprite = {}, sealed = false }, Parts)
end

local function copySprites(src)
    if type(src) ~= "table" then return nil end
    local out, count = {}, 0
    for mask = 0, Grid.ALL do
        local s = src[mask]
        if s ~= nil then
            if type(s) ~= "string" or s == "" then return nil end
            out[mask] = s
            count = count + 1
        end
    end
    if count == 0 then return nil end
    return out
end

-- Sorted list { kind, params, impl } so hooks run in a stable order.
function Parts:copyCapabilities(src)
    if type(src) ~= "table" then return nil, "invalid_capabilities" end
    local list = {}
    for kind, params in pairs(src) do
        local impl = self.capabilities:get(kind)
        if not impl then return nil, "unknown_capability", tostring(kind) end
        if params == true then params = {} end
        local copy, field = impl.define(params)
        if copy == nil then return nil, "invalid_field", kind .. "." .. tostring(field) end
        list[#list + 1] = { kind = kind, params = copy, impl = impl }
    end
    if #list == 0 then return nil, "invalid_capabilities" end
    table.sort(list, function(a, b) return a.kind < b.kind end)
    return list
end

-- Returns true, or false, a reason and sometimes a detail: "registration_closed",
-- "invalid_id", "duplicate_part", "invalid_definition", "invalid_sprites", "duplicate_sprite",
-- "invalid_sides", "invalid_capabilities", "unknown_capability", "invalid_field".
function Parts:register(id, def)
    if self.sealed then return false, "registration_closed" end
    if not Check.isNamespaced(id) then return false, "invalid_id" end
    if self.defs[id] then return false, "duplicate_part" end
    if type(def) ~= "table" then return false, "invalid_definition" end
    local sprites = copySprites(def.sprites)
    if not sprites then return false, "invalid_sprites" end
    for _, s in pairs(sprites) do
        if self.bySprite[s] then return false, "duplicate_sprite", s end
    end
    local sides = def.sides
    if sides == nil then sides = Grid.ALL end
    if not Check.isInteger(sides, 0, Grid.ALL) then return false, "invalid_sides" end
    local caps, reason, detail = self:copyCapabilities(def.capabilities)
    if not caps then return false, reason, detail end
    self.defs[id] = { sprites = sprites, sides = sides, caps = caps }
    for _, s in pairs(sprites) do self.bySprite[s] = id end
    return true
end

function Parts:seal()
    self.sealed = true
end

function Parts:has(id)
    return self.defs[id] ~= nil
end

local function deepCopy(v)
    if type(v) ~= "table" then return v end
    local out = {}
    for k, x in pairs(v) do out[k] = deepCopy(x) end
    return out
end

-- Public description of a part type (a copy), or nil.
function Parts:describe(id)
    local def = self.defs[id]
    if not def then return nil end
    local caps = {}
    for i = 1, #def.caps do caps[def.caps[i].kind] = deepCopy(def.caps[i].params) end
    return { sprites = deepCopy(def.sprites), sides = def.sides, capabilities = caps }
end

return Parts
