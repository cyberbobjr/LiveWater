-- LiveWater: the shared reserve of a house (ADR-001 D28, L02, L03, L06, L07). Pure. Plans how much
-- water each barrel connected to an inlet gives each relay tank that needs some:
--   sources  list of { key, z (level of the barrel), amount, usable (holds only water, or
--            nothing), reserve (taken last), lifted (a pump or power: no gravity rule) }
--   needs    list of { key, z (level of the relay: its fixture is one level below), free }
-- Gravity: a barrel serves the fixtures of its own level and below, unless lifted. The barrels
-- able to serve a relay drain together, each by its share of their water; the barrels kept in
-- reserve only when the others have none left for it. A barrel holding anything but water gives
-- nothing (it stays connected).
-- plan(sources, needs) -> moves { { source = key, need = key, litres } }, reasons { [i] = why need
-- i stays short: "gravity" (water only too low), "empty" (no water), nil (served) }.

local Reserve = {}

Reserve.EPSILON = 0.001

local function reaches(source, need)
    return source.lifted or need.z - 1 <= source.z
end

-- Take up to `want` litres for `need` from the sources of one tier; returns the litres taken.
local function drain(sources, left, need, want, inReserve, moves)
    local total, eligible = 0, {}
    for i = 1, #sources do
        local s = sources[i]
        if (s.reserve == true) == inReserve and left[i] > Reserve.EPSILON and reaches(s, need) then
            eligible[#eligible + 1] = i
            total = total + left[i]
        end
    end
    if total <= Reserve.EPSILON then return 0 end
    local take = math.min(want, total)
    for j = 1, #eligible do
        local i = eligible[j]
        local litres = take * left[i] / total
        left[i] = left[i] - litres
        moves[#moves + 1] = { source = sources[i].key, need = need.key, litres = litres }
    end
    return take
end

-- Why `need` stays short once the sources gave what they could.
local function reasonFor(sources, left)
    for i = 1, #sources do
        if left[i] > Reserve.EPSILON then return "gravity" end
    end
    return "empty"
end

function Reserve.plan(sources, needs)
    local left, moves, reasons = {}, {}, {}
    for i = 1, #sources do
        local s = sources[i]
        left[i] = s.usable and math.max(0, s.amount or 0) or 0
    end
    for n = 1, #needs do
        local need = needs[n]
        local want = need.free
        want = want - drain(sources, left, need, want, false, moves)
        if want > Reserve.EPSILON then want = want - drain(sources, left, need, want, true, moves) end
        if want > Reserve.EPSILON then reasons[n] = reasonFor(sources, left) end
    end
    return moves, reasons
end

return Reserve
