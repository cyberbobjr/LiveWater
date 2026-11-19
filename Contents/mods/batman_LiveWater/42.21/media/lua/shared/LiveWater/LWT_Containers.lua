-- LiveWater: registry of the containers a barrel fitting works with (ADR-001 D26, D28, L08). Pure, no
-- game API. A container is named by the sprite of its object ("carpentry_02_54") or by the name of
-- its entity script ("RainCollector"); its definition is data:
--   shape  "tall" (round barrel, drum, default) or "low" (wide crate collector): picks the sprite
--          of the fitting (barrel_fill or barrel_fill_low, tuiles-contrat.md)
-- Every container takes the network's water like a barrel, tainted (ADR-005 D07); another field of a
-- definition (`clean` of revision 12) is ignored.
-- A fitting works with (admits) any object holding a FluidContainer of MIN_LITRES or more (barrels,
-- rain collectors), and with a smaller one when it is registered (water coolers by default, E25) or
-- listed in the sandbox string option FillContainers (names separated by ";"). An unknown
-- container is tall. Other mods add theirs with LiveWater.API.registerContainer.

local SHAPES = { tall = true, low = true }

-- Litres from which any fluid container is a barrel.
local MIN_LITRES = 20

-- Registered by default whatever their size (vanilla 42.22 entity WaterDispenser, 15 L).
local DEFAULT_SMALL = { "WaterDispenser" }

-- Definition of a container listed in the sandbox option.
local LISTED = { shape = "tall" }

-- Vanilla 42.22 low wide rain collectors (wooden crate with a tarp): entities RainCollector
-- (carpentry_02_54) and RainCollector_Tarp (carpentry_02_120), and their older neighbours.
local LOW_SPRITES = { "carpentry_02_52", "carpentry_02_53", "carpentry_02_54", "carpentry_02_55",
    "carpentry_02_120", "carpentry_02_121" }

local Containers = {}
Containers.__index = Containers

function Containers.new()
    local self = setmetatable({ byName = {}, sealed = false }, Containers)
    for i = 1, #LOW_SPRITES do self.byName[LOW_SPRITES[i]] = { shape = "low" } end
    for i = 1, #DEFAULT_SMALL do self.byName[DEFAULT_SMALL[i]] = { shape = "tall" } end
    return self
end

local function isName(v)
    return type(v) == "string" and #v > 0 and #v <= 120 and string.match(v, "^[%w_:%.]+$") ~= nil
end

-- Returns true, or false and "registration_closed", "invalid_name", "invalid_definition".
function Containers:register(name, def)
    if self.sealed then return false, "registration_closed" end
    if not isName(name) then return false, "invalid_name" end
    if type(def) ~= "table" or (def.shape ~= nil and not SHAPES[def.shape]) then
        return false, "invalid_definition"
    end
    self.byName[name] = { shape = def.shape or "tall" }
    return true
end

function Containers:seal()
    self.sealed = true
end

-- Definition of a container by its sprite, else its entity name; `listed` (optional set of the
-- names of the sandbox option) gives the definition of a listed one; else nil.
function Containers:find(sprite, entity, listed)
    local def = (sprite and self.byName[sprite]) or (entity and self.byName[entity])
    if def then return def end
    if listed and ((sprite and listed[sprite]) or (entity and listed[entity])) then return LISTED end
    return nil
end

-- Does a fitting work with a fluid container of `capacity` litres and these names?
function Containers:admits(capacity, sprite, entity, listed)
    return capacity >= MIN_LITRES or self:find(sprite, entity, listed) ~= nil
end

-- Set of the names of the sandbox string option ("WaterDispenser;my_tiles_3").
function Containers.parseList(text)
    local out = {}
    if type(text) ~= "string" then return out end
    for name in string.gmatch(text, "[^;]+") do
        name = string.match(name, "^%s*(.-)%s*$")
        if name ~= "" then out[name] = true end
    end
    return out
end

-- Shape of a container: registered, else "tall".
function Containers:shapeOf(sprite, entity, listed)
    local def = self:find(sprite, entity, listed)
    return def and def.shape or "tall"
end

return Containers
