-- LiveWater capability "intake": the part takes water from a source (ADR-001 D16, D17).
--   quality   "tainted" (lake, pond, river: default) or "clean": quality of a part that recorded
--             no source kind, or a kind no longer registered
--   orVessel  the part may also stand against a barrel without any source (default false, API
--             revision 21, ADR-011 D01): it then gives no water of its own, only what its `vessel`
--             capability draws from the barrel
-- State: { source = kind of the source found next to the part (LWT_Sources), vessel = true when
-- it stands against a barrel without source }. The water has the quality of that kind (natural
-- water tainted, well clean: P02), asked from ctx.sources.
-- The part stands only next to a source (or a barrel, orVessel): attach records it, or refuses.

local Check = require "LiveWater/LWT_Check"

local SPEC = { quality = Check.oneOf({ clean = true, tainted = true }, "tainted"), orVessel = Check.boolean(false) }

local Intake = {}

function Intake.define(params)
    return Check.fields(params, SPEC)
end

function Intake.attach(p, d, site)
    local kind = site and site:source()
    if kind then
        d.source, d.vessel = kind, nil
        return true
    end
    if p.orVessel and site and site.hasVessel and site:hasVessel() then
        d.source, d.vessel = nil, true
        return true
    end
    return false, "no_source"
end

-- Extension point (D16): the source may run dry later (frost, empty well); always available now.
local function available(p, d, ctx)
    return true
end

function Intake.source(p, d, ctx)
    if d and d.vessel then return nil end
    if not available(p, d, ctx) then return nil end
    local kind, sources = d and d.source, ctx and ctx.sources
    return kind and sources and sources:quality(kind) or p.quality
end

-- Source line (P08): key "IGUI_LWT_Source_<kind>", ":" and other signs of a mod's kind as "_".
function Intake.lines(p, d)
    if not (d and d.source) then return {} end
    return { { "IGUI_LWT_Source_" .. string.gsub(d.source, "[^%w_]", "_"), rank = 40 } }
end

return Intake
