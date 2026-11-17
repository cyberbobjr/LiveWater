-- LiveWater: value checks and whitelist copy of definition fields (pure, no game API).
-- A rule is { default = value, valid = function(v) return bool end }; Check.fields copies only
-- the fields its spec names, so extra fields of the caller never reach LiveWater.

local Check = {}

function Check.isNumber(v, low, high)
    return type(v) == "number" and v == v and v >= low and v <= high
end

function Check.isInteger(v, low, high)
    return Check.isNumber(v, low, high) and v % 1 == 0
end

-- Plain name: letter then letters, digits or underscores.
function Check.isName(v)
    return type(v) == "string" and #v <= 64 and string.match(v, "^%a[%w_]*$") ~= nil
end

-- Namespaced identifier "<Mod>:<Name>" (ADR-001 D03).
function Check.isNamespaced(v)
    return type(v) == "string" and #v <= 120 and string.match(v, "^%a[%w_]*:%a[%w_]*$") ~= nil
end

function Check.number(low, high, default)
    return { default = default, valid = function(v) return Check.isNumber(v, low, high) end }
end

function Check.integer(low, high, default)
    return { default = default, valid = function(v) return Check.isInteger(v, low, high) end }
end

function Check.boolean(default)
    return { default = default, valid = function(v) return type(v) == "boolean" end }
end

-- `allowed` is a set { value = true }.
function Check.oneOf(allowed, default)
    return { default = default, valid = function(v) return allowed[v] == true end }
end

-- Whitelist copy of `params` by `spec` ({ field = rule }). Returns the copy, or nil and the
-- name of the first invalid field ("params" when params is not a table).
function Check.fields(params, spec)
    if type(params) ~= "table" then return nil, "params" end
    local out = {}
    for name, rule in pairs(spec) do
        local v = params[name]
        if v == nil then
            v = rule.default
        elseif not rule.valid(v) then
            return nil, name
        end
        out[name] = v
    end
    return out
end

return Check
