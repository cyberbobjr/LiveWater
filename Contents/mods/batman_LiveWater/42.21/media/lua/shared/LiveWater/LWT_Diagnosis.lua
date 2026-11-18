-- LiveWater: why a fixture has no water, in one line (ADR-001 D28, L09). Pure.
--   inlet(state, short, hasBarrels, pumped) -> reason the relays of an inlet stay empty, or nil:
--       state       what the last network step did with the inlet (LWT_Flow), read only when a
--                   pump is on its network (pumped)
--       short       why its barrels left a relay short (LWT_Reserve: "gravity", "empty"), or nil
--     reasons: "unfiltered", "no_pressure", "no_water", "closed", "wrong_fluid", "gravity", "empty",
--     "no_supply"
--   fixture(info) -> translation key of the line shown at a fixture without water; info =
--       { plumbed (uses an outside source), source = nil, "ours" (a LiveWater relay) or "other",
--         why = reason noted on our relay }

local Diagnosis = {}

-- Network outcomes that leave the house without water.
Diagnosis.NETWORK = { unfiltered = true, no_pressure = true, no_water = true, closed = true, wrong_fluid = true }

function Diagnosis.inlet(state, short, hasBarrels, pumped)
    if pumped and Diagnosis.NETWORK[state] then return state end
    if short then return short end
    if not pumped and not hasBarrels then return "no_supply" end
    return nil
end

function Diagnosis.fixture(info)
    if not info.source then return "IGUI_LWT_Why_NoInlet" end
    if not info.plumbed then return "IGUI_LWT_Why_NotPlumbed" end
    if info.source ~= "ours" then return "IGUI_LWT_Why_Other" end
    if info.why then return "IGUI_LWT_Why_" .. info.why end
    return "IGUI_LWT_Why_Waiting"
end

return Diagnosis
