-- LiveWater: registry of capability kinds (ADR-001 D02). A capability is a strategy: a table
-- of hook functions, copied by whitelist at registration. Every hook takes the checked
-- params of the part definition first. Hooks:
--   define(params)  required: whitelist copy of the params with their defaults, or nil and
--                   the name of the invalid field (params is {} when the part wrote `true`).
-- Optional hooks take (params, data), data being the part's own state for this kind
-- (part.data[kind], possibly nil, ADR-001 D04):
--   carries(p, d)      water goes through the part (network)
--   blocks(p, d)       the part cuts the water now, e.g. a closed valve (network)
--   pressurizes(p, d)  the part puts its network under pressure: water starts there (network)
--   ports(p, d)        most pipes that may leave the part (network)

local Check = require "LiveWater/LWT_Check"

local HOOKS = { "define", "carries", "blocks", "pressurizes", "ports" }

local Capabilities = {}
Capabilities.__index = Capabilities

function Capabilities.new()
    return setmetatable({ impls = {}, sealed = false }, Capabilities)
end

local function isKind(v)
    return Check.isName(v) or Check.isNamespaced(v)
end

local function copyHooks(impl)
    if type(impl) ~= "table" or type(impl.define) ~= "function" then return nil end
    local out = {}
    for i = 1, #HOOKS do
        local hook = impl[HOOKS[i]]
        if hook ~= nil then
            if type(hook) ~= "function" then return nil end
            out[HOOKS[i]] = hook
        end
    end
    return out
end

-- Returns true, or false and "registration_closed", "invalid_kind", "duplicate_capability",
-- "invalid_implementation".
function Capabilities:register(kind, impl)
    if self.sealed then return false, "registration_closed" end
    if not isKind(kind) then return false, "invalid_kind" end
    if self.impls[kind] then return false, "duplicate_capability" end
    local hooks = copyHooks(impl)
    if not hooks then return false, "invalid_implementation" end
    self.impls[kind] = hooks
    return true
end

function Capabilities:get(kind)
    return self.impls[kind]
end

function Capabilities:seal()
    self.sealed = true
end

return Capabilities
