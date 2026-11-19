-- LiveWater: text of the information lines of a part (`lines` hooks, P08), client. Shared by the
-- "Information" tooltip (LWT_PartMenu) and the part windows (LWT_PartWindow): one translated string
-- per line, the sandbox values in the context (watering flow, ADR-006 D09; pump flow).

local GameSettings = require "LiveWater/LWT_GameSettings"

local PartText = {}

-- Context of the `lines` hooks on the client.
PartText.CTX = { scale = GameSettings.scale }

-- Argument of a line as text: a whole number without a decimal part (a Lua number reaches
-- Java's getText as a Double, "50.0").
function PartText.asText(v)
    if type(v) == "number" and v % 1 == 0 then return string.format("%d", v) end
    return tostring(v)
end

-- Translated lines of the part ({ type, data }): list of strings, and the list of their keys.
function PartText.texts(catalog, part)
    local lines, out, keys = catalog:lines(part, PartText.CTX), {}, {}
    for i = 1, #lines do
        local l, args = lines[i], {}
        for j = 2, #l do args[j - 1] = PartText.asText(l[j]) end
        out[i] = getText(l[1], unpack(args))
        keys[i] = l[1]
    end
    return out, keys
end

return PartText
