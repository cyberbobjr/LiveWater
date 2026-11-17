-- LiveWater: registry of the kinds of water source an intake can draw from (ADR-001 D16, D17,
-- P02). Pure, no game API. A kind is data: how it is recognised around the intake and the
-- quality of its water:
--   quality  required: "clean" or "tainted"
--   flag     optional: name of an IsoFlagType a neighbour square carries ("water")
--   sprites  optional: list of sprite names of an object on a neighbour square (a well)
-- At least one of flag and sprites. find(probe) asks a probe of the place (LWT_GameSite, or a
-- test double): probe:hasFlag(name), probe:hasSprite(name). Clean kinds are tried first, then
-- by kind name, so the answer does not depend on registration order.

local Check = require "LiveWater/LWT_Check"

local QUALITIES = { clean = true, tainted = true }

local Sources = {}
Sources.__index = Sources

function Sources.new()
    return setmetatable({ kinds = {}, order = {}, sealed = false }, Sources)
end

local function copySprites(list)
    if list == nil then return {} end
    if type(list) ~= "table" then return nil end
    local out = {}
    for i = 1, #list do
        if type(list[i]) ~= "string" or list[i] == "" then return nil end
        out[i] = list[i]
    end
    return out
end

local function before(a, b)
    if a.quality ~= b.quality then return a.quality == "clean" end
    return a.kind < b.kind
end

-- Returns true, or false and "registration_closed", "invalid_kind", "duplicate_source",
-- "invalid_definition".
function Sources:register(kind, def)
    if self.sealed then return false, "registration_closed" end
    if not (Check.isName(kind) or Check.isNamespaced(kind)) then return false, "invalid_kind" end
    if self.kinds[kind] then return false, "duplicate_source" end
    if type(def) ~= "table" or not QUALITIES[def.quality] then return false, "invalid_definition" end
    local sprites = copySprites(def.sprites)
    if not sprites or (def.flag ~= nil and not Check.isName(def.flag)) then return false, "invalid_definition" end
    if def.flag == nil and #sprites == 0 then return false, "invalid_definition" end
    local entry = { kind = kind, quality = def.quality, flag = def.flag, sprites = sprites }
    self.kinds[kind] = entry
    self.order[#self.order + 1] = entry
    table.sort(self.order, before)
    return true
end

function Sources:seal()
    self.sealed = true
end

-- Quality of the water of a kind, or nil when the kind is not registered.
function Sources:quality(kind)
    local entry = self.kinds[kind]
    return entry and entry.quality or nil
end

local function matches(entry, probe)
    if entry.flag and probe:hasFlag(entry.flag) then return true end
    for i = 1, #entry.sprites do
        if probe:hasSprite(entry.sprites[i]) then return true end
    end
    return false
end

-- Kind of the first source found around the probe, or nil.
function Sources:find(probe)
    for i = 1, #self.order do
        if matches(self.order[i], probe) then return self.order[i].kind end
    end
    return nil
end

return Sources
