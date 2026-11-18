-- LiveWater: registry of part types (ADR-001 D01-D03, D05, D12). Pure, no game API; the
-- capability registry is injected. A definition is copied by whitelist:
--   sprites       { [mask] = spriteName } for masks 0..15 (side mask of LWT_Grid), redrawn when
--                 the links change; required unless `variants` is given
--   variants      optional (API revision 2): { [key] = { spriteName, ... } } sprites drawn by the
--                 state of the part: key = the look of the part (Parts:look, e.g. "on",
--                 "filter_off"), list index = facing 1..4 (S, E, N, W). Never redrawn by the mask.
--                 A sprite belongs to one part type only (sprites and variants together).
--   facings       optional (API revision 13): { [mask] = facing 1..4 } the variant facing drawn
--                 for a side mask (an inline part turned along its pipe: a valve); a mask without
--                 one keeps the facing the part shows
--   sides         optional: mask of the sides the part may connect by (default 15)
--   capabilities  required: { kind = params or true }, every kind registered, params checked
--                 by the kind's define hook
-- Placed parts carry their type in `part.type`; this registry is also the catalog the domain
-- modules (network, flow) ask about a part, without knowing any kind by name.

local Check = require "LiveWater/LWT_Check"
local Grid = require "LiveWater/LWT_Grid"

local Parts = {}
Parts.__index = Parts

Parts.MAX_FACINGS = 4

function Parts.new(capabilities)
    return setmetatable({ capabilities = capabilities, defs = {}, bySprite = {}, facing = {}, sealed = false }, Parts)
end

local function isSpriteName(s)
    return type(s) == "string" and s ~= ""
end

local function copySprites(src)
    if type(src) ~= "table" then return nil end
    local out, count = {}, 0
    for mask = 0, Grid.ALL do
        local s = src[mask]
        if s ~= nil then
            if not isSpriteName(s) then return nil end
            out[mask] = s
            count = count + 1
        end
    end
    if count == 0 then return nil end
    return out
end

-- Copy of the variants ({} when absent) and how many sprites they hold, or nil when invalid.
local function copyVariants(src)
    if src == nil then return {}, 0 end
    if type(src) ~= "table" then return nil end
    local out, count = {}, 0
    for key, list in pairs(src) do
        if not Check.isName(key) or type(list) ~= "table" or #list < 1 or #list > Parts.MAX_FACINGS then return nil end
        local copy = {}
        for i = 1, #list do
            if not isSpriteName(list[i]) then return nil end
            copy[i] = list[i]
        end
        out[key] = copy
        count = count + #copy
    end
    return out, count
end

-- Copy of the facings by mask ({} when absent), or nil when invalid.
local function copyFacings(src)
    if src == nil then return {} end
    if type(src) ~= "table" then return nil end
    local out = {}
    for mask, facing in pairs(src) do
        if not Check.isInteger(mask, 0, Grid.ALL) or not Check.isInteger(facing, 1, Parts.MAX_FACINGS) then return nil end
        out[mask] = facing
    end
    return out
end

-- Every sprite name of a definition: list of { name, facing or nil }.
local function allSprites(sprites, variants)
    local list = {}
    for _, s in pairs(sprites) do list[#list + 1] = { s } end
    for _, l in pairs(variants) do
        for i = 1, #l do list[#list + 1] = { l[i], i } end
    end
    return list
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
-- "invalid_id", "duplicate_part", "invalid_definition", "invalid_sprites", "invalid_variants",
-- "duplicate_sprite", "invalid_facings", "invalid_sides", "invalid_capabilities", "unknown_capability", "invalid_field".
function Parts:register(id, def)
    if self.sealed then return false, "registration_closed" end
    if not Check.isNamespaced(id) then return false, "invalid_id" end
    if self.defs[id] then return false, "duplicate_part" end
    if type(def) ~= "table" then return false, "invalid_definition" end
    local variants, variantCount = copyVariants(def.variants)
    if not variants then return false, "invalid_variants" end
    local sprites = copySprites(def.sprites)
    if not sprites then
        if def.sprites ~= nil or variantCount == 0 then return false, "invalid_sprites" end
        sprites = {}
    end
    local names = allSprites(sprites, variants)
    for i = 1, #names do
        if self.bySprite[names[i][1]] then return false, "duplicate_sprite", names[i][1] end
    end
    local facings = copyFacings(def.facings)
    if not facings then return false, "invalid_facings" end
    local sides = def.sides
    if sides == nil then sides = Grid.ALL end
    if not Check.isInteger(sides, 0, Grid.ALL) then return false, "invalid_sides" end
    local caps, reason, detail = self:copyCapabilities(def.capabilities)
    if not caps then return false, reason, detail end
    self.defs[id] = { sprites = sprites, variants = variants, facings = facings, sides = sides, caps = caps }
    for i = 1, #names do
        self.bySprite[names[i][1]] = id
        if names[i][2] then self.facing[names[i][1]] = names[i][2] end
    end
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

-- ---------------------------------------------------------------- catalog of placed parts
-- A placed part is { type = id, data = { [kind] = state } , ... }; a part whose type is not
-- registered answers nothing (inert, D03).

function Parts:sides(id)
    local def = self.defs[id]
    return def and def.sides or 0
end

-- Sprite of the type for a side mask: sprites[mask], else sprites[0] (nil when neither).
function Parts:sprite(id, mask)
    local def = self.defs[id]
    if not def then return nil end
    return def.sprites[mask] or def.sprites[0]
end

-- Does the type draw its own sprite for this mask (a pipe shape)? A type that does not keeps
-- the sprite it was placed with, e.g. an orientation chosen at placement.
function Parts:hasShape(id, mask)
    local def = self.defs[id]
    return def ~= nil and def.sprites[mask] ~= nil
end

-- Type id a sprite belongs to, or nil (sprites are unique among types, variants included).
function Parts:typeOfSprite(name)
    return self.bySprite[name]
end

-- Facing (1..4) of a variant sprite, or nil.
function Parts:facingOf(name)
    return self.facing[name]
end

-- Variant facing the type draws for a side mask (field `facings`), or nil.
function Parts:facingFor(id, mask)
    local def = self.defs[id]
    return def and def.facings[mask] or nil
end

-- Sprite of the variant `key` of a type for a facing (the first facing when it has fewer), or nil.
function Parts:variant(id, key, facing)
    local def = self.defs[id]
    local list = def and def.variants[key]
    if not list then return nil end
    return list[facing or 1] or list[1]
end

-- Every sprite name of a type (shapes and variants), sorted, without duplicates.
function Parts:spritesOf(id)
    local def, seen, list = self.defs[id], {}, {}
    if not def then return list end
    local names = allSprites(def.sprites, def.variants)
    for i = 1, #names do
        if not seen[names[i][1]] then
            seen[names[i][1]] = true
            list[#list + 1] = names[i][1]
        end
    end
    table.sort(list)
    return list
end

-- Does one capability of the type have this hook?
function Parts:hasHook(id, hook)
    local def = self.defs[id]
    if not def then return false end
    for i = 1, #def.caps do
        if def.caps[i].impl[hook] then return true end
    end
    return false
end

-- Registered type ids, sorted.
function Parts:ids()
    local list = {}
    for id in pairs(self.defs) do list[#list + 1] = id end
    table.sort(list)
    return list
end

local function stateOf(part, kind)
    return part.data and part.data[kind]
end

-- State table of one capability of the part, created under part.data[kind] when absent.
local function ownState(part, kind)
    part.data = part.data or {}
    local state = part.data[kind]
    if state == nil then
        state = {}
        part.data[kind] = state
    end
    return state
end

-- True when one capability of the part answers `hook` with a true value.
function Parts:any(part, hook, ...)
    local def = self.defs[part.type]
    if not def then return false end
    for i = 1, #def.caps do
        local c = def.caps[i]
        local fn = c.impl[hook]
        if fn and fn(c.params, stateOf(part, c.kind), ...) then return true end
    end
    return false
end

-- Is the part closed now? One capability blocks the water (a closed valve) and none holds it open
-- (a timer watering, `opens` hook, API revision 9).
function Parts:closed(part)
    return self:any(part, "blocks") and not self:any(part, "opens")
end

-- Results (up to four) of the first capability of the part whose `hook` answers non-nil, or nil.
function Parts:first(part, hook, ...)
    local def = self.defs[part.type]
    if not def then return nil end
    for i = 1, #def.caps do
        local c = def.caps[i]
        local fn = c.impl[hook]
        if fn then
            local a, b, d, e = fn(c.params, stateOf(part, c.kind), ...)
            if a ~= nil then return a, b, d, e end
        end
    end
    return nil
end

-- Call `hook` on every capability of the part that has it, giving each its own state table
-- (created under part.data[kind] when absent): for hooks that change the state.
function Parts:call(part, hook, ...)
    local def = self.defs[part.type]
    if not def then return end
    for i = 1, #def.caps do
        local c = def.caps[i]
        local fn = c.impl[hook]
        if fn then fn(c.params, ownState(part, c.kind), ...) end
    end
end

-- Look of a part: the tokens its capabilities answer to `look` (in kind order) joined by "_",
-- e.g. "filter" and "on" give "filter_on"; nil when none answers. Picks the variant drawn.
function Parts:look(part)
    local def = self.defs[part.type]
    if not def then return nil end
    local tokens = {}
    for i = 1, #def.caps do
        local c = def.caps[i]
        local fn = c.impl.look
        local token = fn and fn(c.params, stateOf(part, c.kind))
        if token then tokens[#tokens + 1] = token end
    end
    if #tokens == 0 then return nil end
    return table.concat(tokens, "_")
end

-- Can the part stand where `site` is (port of the place, see LWT_GameSite)? Every capability
-- with an `attach` hook may refuse, or record what it found in its own state. Returns true, or
-- false and the reason of the first refusal ("unknown_part" for a type not registered).
function Parts:attach(part, site)
    local def = self.defs[part.type]
    if not def then return false, "unknown_part" end
    for i = 1, #def.caps do
        local c = def.caps[i]
        if c.impl.attach then
            local ok, reason = c.impl.attach(c.params, ownState(part, c.kind), site)
            if not ok then return false, reason end
        end
    end
    return true
end

-- Text lines the part shows (information, Live Wire): { { key, arg, ... }, ... } gathered from
-- the `lines` hooks, sorted by their `rank` field (default 50, then kind order), rank dropped.
function Parts:lines(part)
    local def = self.defs[part.type]
    local found = {}
    if not def then return found end
    for i = 1, #def.caps do
        local c = def.caps[i]
        local fn = c.impl.lines
        local list = fn and fn(c.params, stateOf(part, c.kind)) or {}
        for j = 1, #list do
            found[#found + 1] = { line = list[j], rank = list[j].rank or 50, n = #found }
        end
    end
    table.sort(found, function(a, b)
        if a.rank ~= b.rank then return a.rank < b.rank end
        return a.n < b.n
    end)
    local out = {}
    for i = 1, #found do
        local line = {}
        for j = 1, #found[i].line do line[j] = found[i].line[j] end
        out[i] = line
    end
    return out
end

-- Actions the part menu offers for the part: the `actions` lists of its capabilities, in kind
-- order; action = { command, key, item = full type the player must carry, or nil, choices = list
-- of { key, arg, args } offered as a submenu (revision 9: the chosen args go with the command),
-- or nil }.
function Parts:actions(part)
    local def = self.defs[part.type]
    local out = {}
    if not def then return out end
    for i = 1, #def.caps do
        local c = def.caps[i]
        local fn = c.impl.actions
        local list = fn and fn(c.params, stateOf(part, c.kind)) or {}
        for j = 1, #list do
            out[#out + 1] = { command = list[j].command, key = list[j].key, item = list[j].item,
                choices = deepCopy(list[j].choices) }
        end
    end
    return out
end

-- Public description of a part type (a copy), or nil.
function Parts:describe(id)
    local def = self.defs[id]
    if not def then return nil end
    local caps = {}
    for i = 1, #def.caps do caps[def.caps[i].kind] = deepCopy(def.caps[i].params) end
    return { sprites = deepCopy(def.sprites), variants = deepCopy(def.variants),
        facings = deepCopy(def.facings), sides = def.sides, capabilities = caps }
end

return Parts
