-- LiveWater: the state a part keeps of the container set against it, as the authority senses it
-- (server LWT_Fittings, `sense` hook, ADR-001 D26, ADR-011 D02). Pure, shared by the capabilities
-- that work with a container (fitting, vessel).
--   record(d, info)  copy of the sensed info into the part's state d: found, shape, fluid, amount,
--                    free, share, cx, cy, cz, offline, blocked (why nothing may go in: "feed", a
--                    trough holding feed, ADR-013 D04), takes (what it takes even empty: "water"
--                    for a feeding trough, ADR-014 D04)

local Sensed = {}

function Sensed.record(d, info)
    d.found = info.found == true
    d.shape, d.fluid, d.amount, d.free, d.share = info.shape, info.fluid, info.amount, info.free, info.share
    d.cx, d.cy, d.cz = info.cx, info.cy, info.cz
    d.offline = info.offline
    d.blocked = info.blocked
    d.takes = info.takes
end

return Sensed
