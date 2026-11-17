-- LiveWater: one ten-minute distribution step of a network (ADR-001 D09, D13-D17). Pure, no
-- game API: the catalog of part types is injected, the network (LWT_Network) and the need of
-- each outlet (ctx.need(part) -> litres, from the adapters) are given to step.
-- Rules:
--   the parts that pressurize add their pressure and their litres (D15); litres count only
--   when the part has a source of water; the water is tainted when one source is tainted;
--   outlets are taken in service order (pipe distance, then placement order, D14):
--     closed (blocks)          -> "closed"
--     no need                  -> "idle", takes nothing (D09)
--     no water left            -> "no_water"
--     needs clean water and the water reaching it is not clean -> "unfiltered" (D17)
--     the pressure left is too low, or was too low for an earlier outlet -> "no_pressure"
--     else                     -> "served": min(need, water left) litres, pressure taken;
--   the first working filter on the way from the pump (outlet included) makes the water clean
--   and wears by the litres served through it;
--   every part on the way of the water served is credited those litres and their quality
--   (through, qualityAt by key: clean from the filter on, the network's water before it); a
--   pressurizing part is credited its share of all the water served instead.
-- The context `ctx` is passed to the hooks supply, source, purifies and wear (LWT_Settings).

local Flow = {}
Flow.__index = Flow

Flow.CLEAN, Flow.TAINTED = "clean", "tainted"

function Flow.new(catalog)
    return setmetatable({ catalog = catalog }, Flow)
end

local function mix(a, b)
    if a == Flow.TAINTED or b == Flow.TAINTED then return Flow.TAINTED end
    return b
end

-- Pressure, litres and quality the pressurizing parts give this step, and the litres of each
-- (by key).
function Flow:supply(nodes, ctx)
    local pressure, water, quality, given = 0, 0, nil, {}
    for i = 1, #nodes do
        local part = nodes[i].part
        if nodes[i].root then
            local p, litres = self.catalog:first(part, "supply", ctx)
            pressure = pressure + (p or 0)
            local q = self.catalog:first(part, "source", ctx)
            if q and litres and litres > 0 then
                water = water + litres
                quality = mix(quality, q)
                given[nodes[i].key] = litres
            end
        end
    end
    return pressure, water, quality, given
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

-- State, litres and quality for one outlet of pressure `cost`; `left` holds the water and
-- pressure left; the litres served are routed into `result`.
function Flow:serve(node, cost, needsClean, byKey, left, ctx, result)
    local catalog, part = self.catalog, node.part
    if catalog:any(part, "blocks") then return "closed", 0 end
    local need = ctx.need(part) or 0
    if need <= 0 then return "idle", 0 end
    if left.water <= 0 then return "no_water", 0 end
    local filter = self:purifierOf(node, byKey, ctx)
    local quality = filter and Flow.CLEAN or left.quality
    if needsClean and quality ~= Flow.CLEAN then return "unfiltered", 0 end
    if left.starved or left.pressure < cost then
        left.starved = true
        return "no_pressure", 0
    end
    local litres = math.min(need, left.water)
    left.water, left.pressure = left.water - litres, left.pressure - cost
    if filter then catalog:call(filter, "wear", litres, ctx) end
    self:route(node, byKey, litres, left.quality, filter, result)
    return "served", litres, quality
end

-- One step of network `id`. Returns { pressure, water, quality, served = litres, outlets = list
-- in service order, at = by key, through = litres by key, qualityAt = quality by key }, outlet =
-- { key, part, state, litres, quality }.
function Flow:step(network, id, ctx)
    local nodes, byKey = network:reach(id)
    local pressure, water, quality, given = self:supply(nodes, ctx)
    local result = { pressure = pressure, water = water, quality = quality, served = 0, outlets = {}, at = {},
        through = {}, qualityAt = {} }
    local left = { pressure = pressure, water = water, quality = quality, starved = false }
    for i = 1, #nodes do
        local node = nodes[i]
        local cost, needsClean = self.catalog:first(node.part, "outlet")
        if cost then
            local state, litres, q = self:serve(node, cost, needsClean, byKey, left, ctx, result)
            local out = { key = node.key, part = node.part, state = state, litres = litres, quality = q }
            result.outlets[#result.outlets + 1] = out
            result.at[node.key] = out
            result.served = result.served + litres
        end
    end
    for key, litres in pairs(given) do result.through[key] = litres * result.served / water end
    return result
end

return Flow
