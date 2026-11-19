-- LiveWater: one ten-minute distribution step of a network (ADR-001 D09, D13-D17). Pure, no
-- game API: the catalog of part types is injected, the network (LWT_Network) and the need of
-- each outlet (ctx.need(part) -> litres, from the adapters) are given to step.
-- Rules:
--   each zone of the network (roots that reach one another through open parts; a closed valve
--   between two pumps makes two zones, D02) is served on its own, by the rules below;
--   only the parts that pressurize (the pumps, producers) put water in a network (ADR-012 D01, D03:
--   a network without pump gives nothing); they add their pressure and their litres (D15);
--   a pump that draws (`draw` hook: a pond pump against a barrel, capability "vessel", ADR-011)
--   gives the water of its own barrel: min(its litres, what the barrel gives), of the barrel's
--   quality, taken from that barrel only (drawn); its barrel empty or gone, it gives its own
--   source; a pump gives its litres only when it has a source of water (`source` hook);
--   a pump against a gas station fuel pump draws its fuel the same way (ADR-014 D01);
--   one fluid family per zone and step (ADR-014 D02): the first pump in placement order (the roots
--   come first in the service order, then by placement) that gives something sets the family; a
--   pump whose fluid is of another family gives nothing this step, draws nothing, and is told so
--   (outcome otherFluid);
--   the water of the zone is the sum of what its pumps give, tainted when one of them is tainted;
--   fluids: "clean" and "tainted" water, "fuel", any other quality a third-party part gives is
--   another fluid (family "other"); a filter purifies water only;
--   outlets are taken in service order (pipe distance, then placement order, D14):
--     closed (Parts:closed)    -> "closed"
--     no need                  -> "idle", takes nothing (D09)
--     no water left            -> "no_water"
--     the outlet does not take this fluid (4th result of `outlet`: nil = water only (clean or tainted), "any",
--     "water", "fuel", "other") -> "wrong_fluid"
--     needs clean water and the water reaching it is not clean -> "unfiltered" (D17)
--     the pressure left is too low, or was too low for an earlier outlet -> "no_pressure"
--     else                     -> "served": min(need, water left) litres, pressure taken;
--   the outlets of one cost group (`costGroup` hook, a drip line, ADR-004 D04) pay their cost
--   once per step: the first served pays, the next ones of the group pay nothing;
--   the first working filter on the way from the pump (outlet included) makes the water clean
--   and wears by the litres served through it;
--   every part on the way of the water served is credited those litres and their quality
--   (through, qualityAt by key: clean from the filter on, the network's water before it); a
--   pressurizing part is credited its share of all the water served instead.
-- The context `ctx` is passed to the hooks supply, source, purifies and wear (LWT_Settings).

local Flow = {}
Flow.__index = Flow

Flow.CLEAN, Flow.TAINTED, Flow.FUEL = "clean", "tainted", "fuel"

local FAMILIES = { [Flow.CLEAN] = "water", [Flow.TAINTED] = "water", [Flow.FUEL] = "fuel" }

-- Fluid family of a quality: "water" (clean, tainted), "fuel", else "other" (ADR-005 D03).
function Flow.family(q)
    return FAMILIES[q] or "other"
end

function Flow.new(catalog)
    return setmetatable({ catalog = catalog }, Flow)
end

local function mix(a, b)
    if a == Flow.TAINTED or b == Flow.TAINTED then return Flow.TAINTED end
    return b
end

-- Quality of two waters met (either may be nil).
local function join(a, b)
    if a == nil then return b end
    if b == nil then return a end
    return mix(a, b)
end

-- What a pump gives this step: its own barrel's water first (`draw`), else its source; litres,
-- quality and whether they come from its barrel; 0 without water.
function Flow:produce(part, litres, ctx)
    local barrel, q = self.catalog:first(part, "draw", ctx)
    if barrel and barrel > 0 and q then return math.min(litres, barrel), q, true end
    q = self.catalog:first(part, "source", ctx)
    if q then return litres, q, false end
    return 0, nil, false
end

-- Pressure, litres and quality the pumps of a zone give this step, the litres of each pump (by
-- key), the litres each pump drew from its own barrel (by key) and the pumps that gave nothing
-- because another fluid family is in the pipes (set of keys, D02: the first pump that gives, in
-- the order of `nodes`, sets the family).
function Flow:supply(nodes, ctx)
    local pressure, water, quality, given, drawn, other = 0, 0, nil, {}, {}, {}
    for i = 1, #nodes do
        if nodes[i].root then
            local part, key = nodes[i].part, nodes[i].key
            local p, litres = self.catalog:first(part, "supply", ctx)
            pressure = pressure + (p or 0)
            if litres and litres > 0 then
                local gives, q, fromBarrel = self:produce(part, litres, ctx)
                if gives > 0 and quality and Flow.family(q) ~= Flow.family(quality) then
                    other[key] = true
                elseif gives > 0 then
                    water, quality, given[key] = water + gives, join(quality, q), gives
                    if fromBarrel then drawn[key] = gives end
                end
            end
        end
    end
    return pressure, water, quality, given, drawn, other
end

-- First part on the way from the pump to `node`, node included, whose filter works now.
function Flow:purifierOf(node, byKey, ctx)
    while node do
        if self.catalog:any(node.part, "purifies", ctx) then return node.part end
        node = node.from and byKey[node.from]
    end
    return nil
end

-- Credit `litres` to every node from `node` back to its pressurizing part: clean from the
-- filter (included) to the outlet, `raw` before it.
function Flow:route(node, byKey, litres, raw, filter, result)
    local quality = filter and Flow.CLEAN or raw
    while node do
        result.through[node.key] = (result.through[node.key] or 0) + litres
        result.qualityAt[node.key] = mix(result.qualityAt[node.key], quality)
        if node.part == filter then quality = raw end
        node = node.from and byKey[node.from]
    end
end

-- Does an outlet that takes `holds` (4th result of `outlet`) take this quality?
local function takes(holds, q)
    local family = Flow.family(q)
    if holds == nil then return family == "water" end
    return holds == "any" or holds == family
end

-- Terms of an outlet: { cost, needsClean, holds (4th result of `outlet`), group (cost group or
-- nil) }, or nil for a part that is not one.
function Flow:termsOf(part)
    local cost, needsClean, _, holds = self.catalog:first(part, "outlet")
    if not cost then return nil end
    return { cost = cost, needsClean = needsClean, holds = holds, group = self.catalog:first(part, "costGroup") }
end

-- State, litres and quality for one outlet of `terms`; `left` holds the water and pressure left
-- and the cost groups already paid; the litres served are routed into `result`.
function Flow:serve(node, terms, byKey, left, ctx, result)
    local catalog, part = self.catalog, node.part
    if catalog:closed(part) then return "closed", 0 end
    local need = ctx.need(part) or 0
    if need <= 0 then return "idle", 0 end
    if left.water <= 0 then return "no_water", 0 end
    if not takes(terms.holds, left.quality) then return "wrong_fluid", 0 end
    local filter = Flow.family(left.quality) == "water" and self:purifierOf(node, byKey, ctx) or nil
    local quality = filter and Flow.CLEAN or left.quality
    if terms.needsClean and quality ~= Flow.CLEAN then return "unfiltered", 0 end
    local cost = terms.cost
    if terms.group and left.paid[terms.group] then cost = 0 end
    if left.starved or left.pressure < cost then
        left.starved = true
        return "no_pressure", 0
    end
    local litres = math.min(need, left.water)
    left.water, left.pressure = left.water - litres, left.pressure - cost
    if terms.group then left.paid[terms.group] = true end
    if filter then catalog:call(filter, "wear", litres, ctx) end
    self:route(node, byKey, litres, left.quality, filter, result)
    return "served", litres, quality
end

-- Supply of a zone (roots whose water meets, Network:reach): { water, given, drawn, other, served,
-- left = the water and pressure left (Flow:serve) }.
function Flow:zone(nodes, ctx)
    local pressure, water, quality, given, drawn, other = self:supply(nodes, ctx)
    return { water = water, given = given, drawn = drawn, other = other, served = 0,
        left = { pressure = pressure, water = water, quality = quality, starved = false, paid = {} } }
end

-- Nodes grouped by zone: lists by zone key, and the zone keys in the order of their first node.
local function zonesOf(nodes)
    local byZone, order = {}, {}
    for i = 1, #nodes do
        local z = nodes[i].zone
        if not byZone[z] then
            byZone[z] = {}
            order[#order + 1] = z
        end
        local list = byZone[z]
        list[#list + 1] = nodes[i]
    end
    return byZone, order
end

-- One step of network `id`. Each zone (roots that reach one another through open parts, ADR-001
-- D02, D15: two pumps on each side of a closed valve are two zones) serves its outlets with its own
-- pressure and water. Returns { pressure, water, quality (all zones), served = litres, outlets =
-- list in service order, at = by key, through = litres by key, qualityAt = quality by key, drawn =
-- by key { part, litres } taken from the barrels the pumps draw, otherFluid = set of the keys of the
-- pumps that gave nothing because another fluid is in the pipes (ADR-014 D02) }, outlet = { key,
-- part, state, litres, quality }.
function Flow:step(network, id, ctx)
    local nodes, byKey = network:reach(id)
    local result = { pressure = 0, water = 0, quality = nil, served = 0, outlets = {}, at = {},
        through = {}, qualityAt = {}, drawn = {}, otherFluid = {} }
    local grouped, order = zonesOf(nodes)
    local zones = {}
    for i = 1, #order do
        local zone = self:zone(grouped[order[i]], ctx)
        zones[order[i]] = zone
        result.pressure = result.pressure + zone.left.pressure
        result.water = result.water + zone.water
        if zone.left.quality then result.quality = mix(result.quality, zone.left.quality) end
        for key in pairs(zone.other) do result.otherFluid[key] = true end
    end
    for i = 1, #nodes do
        local node = nodes[i]
        local terms = self:termsOf(node.part)
        if terms then
            local zone = zones[node.zone]
            local state, litres, q = self:serve(node, terms, byKey, zone.left, ctx, result)
            local out = { key = node.key, part = node.part, state = state, litres = litres, quality = q }
            result.outlets[#result.outlets + 1] = out
            result.at[node.key] = out
            result.served = result.served + litres
            zone.served = zone.served + litres
        end
    end
    -- outlets a closed valve keeps dry are "closed" too (the fixture menu says why, L09)
    local behind = network:behindClosed(byKey)
    for i = 1, #behind do
        local node = behind[i]
        if self.catalog:first(node.part, "outlet") then
            local out = { key = node.key, part = node.part, state = "closed", litres = 0 }
            result.outlets[#result.outlets + 1] = out
            result.at[node.key] = out
        end
    end
    for i = 1, #order do
        local zone = zones[order[i]]
        if zone.water > 0 then
            for key, litres in pairs(zone.given) do result.through[key] = litres * zone.served / zone.water end
            for key, litres in pairs(zone.drawn) do
                local taken = litres * zone.served / zone.water
                result.through[key] = taken
                result.drawn[key] = { part = byKey[key].part, litres = taken }
            end
        end
    end
    return result
end

return Flow
