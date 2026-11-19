-- LiveWater: one ten-minute distribution step of a network (ADR-001 D09, D13-D17). Pure, no
-- game API: the catalog of part types is injected, the network (LWT_Network) and the need of
-- each outlet (ctx.need(part) -> litres, from the adapters) are given to step.
-- Rules:
--   each zone of the network (roots that reach one another through open parts; a closed valve
--   between two pumps makes two zones, D02) is served on its own, by the rules below;
--   the parts that pressurize add their pressure and their litres (D15); litres count only
--   when the part has a source of water; the water is tainted when one source is tainted;
--   parts reached that draw (`draw` hook: a barrel fitting set to Pump, D26) replace the pumps'
--   own sources when they hold something: the pumps move up to their litres from them, nearest
--   first, one fluid per network (the fluid of the nearest; others give nothing this step);
--   fluids: "clean" and "tainted" water, "fuel", any other quality a third-party part gives is
--   another fluid (family "other"); a filter purifies water only;
--   outlets are taken in service order (pipe distance, then placement order, D14):
--     closed (Parts:closed)    -> "closed"
--     no need                  -> "idle", takes nothing (D09)
--     no water left            -> "no_water"
--     the outlet does not take this fluid (4th result of `outlet`: nil = water only (clean or tainted), "any",
--     "water", "fuel", "other") -> "wrong_fluid"
--     needs clean water and the water reaching it is not clean -> "unfiltered" (D17)
--     the network runs on gravity and the outlet does not work on it -> "no_pressure"
--     the pressure left is too low, or was too low for an earlier outlet -> "no_pressure"
--     else                     -> "served": min(need, water left) litres, pressure taken;
--   the outlets of one cost group (`costGroup` hook, a drip line, ADR-004 D04) pay their cost
--   once per step: the first served pays, the next ones of the group pay nothing;
--   gravity (ADR-004 D04): on a network without any part that pressurizes, the parts that give
--   gravity pressure (`gravity` hook: a barrel fitting set to Pump) are where the water starts:
--   pressure = the highest they give, water = what they hold (`draw`, no pump capacity); only the
--   outlets that work on gravity (`byGravity` hook) take it;
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

-- Litres the parts that draw give (nearest first, one fluid family, at most `capacity`, no limit
-- when nil): water, quality and the litres of each (by key), or 0 when none holds anything.
function Flow:draws(nodes, capacity, ctx)
    local water, quality, drawn, family = 0, nil, {}, nil
    for i = 1, #nodes do
        local litres, q = self.catalog:first(nodes[i].part, "draw", ctx)
        if litres and litres > 0 and q and (family == nil or Flow.family(q) == family) then
            family = Flow.family(q)
            local take = capacity and math.min(litres, capacity - water) or litres
            if take > 0 then
                water = water + take
                quality = mix(quality, q)
                drawn[nodes[i].key] = take
            end
        end
    end
    return water, quality, drawn
end

-- Pressure, litres and quality the pressurizing parts give this step, the litres of each
-- pressurizing part (by key) and the litres drawn from each part that draws (by key).
function Flow:supply(nodes, ctx)
    local pressure, water, quality, given, capacity, own = 0, 0, nil, {}, 0, {}
    for i = 1, #nodes do
        local part = nodes[i].part
        if nodes[i].root then
            local p, litres = self.catalog:first(part, "supply", ctx)
            pressure = pressure + (p or 0)
            if litres and litres > 0 then
                capacity = capacity + litres
                own[nodes[i].key] = litres
                local q = self.catalog:first(part, "source", ctx)
                if q then
                    water = water + litres
                    quality = mix(quality, q)
                    given[nodes[i].key] = litres
                end
            end
        end
    end
    if pressure <= 0 or capacity <= 0 then return pressure, water, quality, given, {} end
    local drawnWater, drawnQuality, drawn = self:draws(nodes, capacity, ctx)
    if drawnWater <= 0 then return pressure, water, quality, given, {} end
    for key, litres in pairs(own) do own[key] = litres * drawnWater / capacity end
    return pressure, drawnWater, drawnQuality, own, drawn
end

-- Gravity supply of a network without pump (`nodes` reached from the parts that give gravity
-- pressure): pressure (the highest given), litres, quality and the litres drawn from each part (by key).
function Flow:gravity(nodes, ctx)
    local pressure = 0
    for i = 1, #nodes do
        if nodes[i].root then
            local p = self.catalog:first(nodes[i].part, "gravity", ctx)
            if p and p > pressure then pressure = p end
        end
    end
    if pressure <= 0 then return 0, 0, nil, {} end
    local water, quality, drawn = self:draws(nodes, nil, ctx)
    return pressure, water, quality, drawn
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
-- nil), byGravity }, or nil for a part that is not one.
function Flow:termsOf(part)
    local cost, needsClean, _, holds = self.catalog:first(part, "outlet")
    if not cost then return nil end
    return { cost = cost, needsClean = needsClean, holds = holds, group = self.catalog:first(part, "costGroup"),
        byGravity = self.catalog:any(part, "byGravity") }
end

-- State, litres and quality for one outlet of `terms`; `left` holds the water and pressure left,
-- whether the network runs on gravity and the cost groups already paid; the litres served are
-- routed into `result`.
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
    if left.gravity and not terms.byGravity then return "no_pressure", 0 end
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

-- Supply of a zone (roots whose water meets, Network:reach): { water, given, drawn, served, left =
-- the water and pressure left (Flow:serve) }.
function Flow:zone(nodes, gravity, ctx)
    local pressure, water, quality, given, drawn
    if gravity then
        pressure, water, quality, drawn = self:gravity(nodes, ctx)
        given = {}
    else
        pressure, water, quality, given, drawn = self:supply(nodes, ctx)
    end
    return { water = water, given = given, drawn = drawn, served = 0,
        left = { pressure = pressure, water = water, quality = quality, starved = false, gravity = gravity,
            paid = {} } }
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
-- by key { part, litres } taken from the parts that draw, gravity = true when the network ran on
-- gravity }, outlet = { key, part, state, litres, quality }.
function Flow:step(network, id, ctx)
    local nodes, byKey = network:reach(id)
    local gravity = #nodes == 0
    if gravity then nodes, byKey = network:reach(id, "gravity") end
    local result = { pressure = 0, water = 0, quality = nil, served = 0, outlets = {}, at = {},
        through = {}, qualityAt = {}, drawn = {}, gravity = gravity }
    local grouped, order = zonesOf(nodes)
    local zones = {}
    for i = 1, #order do
        local zone = self:zone(grouped[order[i]], gravity, ctx)
        zones[order[i]] = zone
        result.pressure = result.pressure + zone.left.pressure
        result.water = result.water + zone.water
        if zone.left.quality then result.quality = mix(result.quality, zone.left.quality) end
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
