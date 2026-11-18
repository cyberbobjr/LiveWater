if isClient() then return end
-- LiveWater: the plants a sprinkler waters, on the authority (ADR-001 D19, P13). Handler of the outlet
-- type "sprinkler" (LWT_Outlets):
--   need(part)              litres of the doses the plants in its radius need now
--   deliver(part, litres)   gives the plants whole doses of those litres, nearest first
-- A plant needs water when it is alive and its water level is under the level its stage needs
-- (vanilla SPlantGlobalObject waterLvl < waterNeeded); one dose raises the level by DOSE_POINTS
-- (vanilla SPlantGlobalObject:water, +10 per use), so it needs ceil((needed - level) / 10) doses.
-- Radius and dose come from the part's `spray` capability. No game API here; dependencies are
-- injected: { catalog, farming (port: plant(x, y, z) -> { alive, level, needed } or nil;
-- water(x, y, z, doses)), scale (optional: function(optionName) -> sandbox value) }.

local Plants = {}
Plants.__index = Plants

Plants.DOSE_POINTS = 10
local EPSILON = 0.000001

function Plants.new(deps)
    return setmetatable({ catalog = deps.catalog, farming = deps.farming, ctx = { scale = deps.scale } }, Plants)
end

-- Doses a plant needs now (0 when none).
function Plants.dosesFor(plant)
    if not plant or not plant.alive then return 0 end
    local missing = (plant.needed or 0) - (plant.level or 0)
    if missing <= 0 then return 0 end
    return math.ceil(missing / Plants.DOSE_POINTS)
end

-- Plants in the radius of the part that need water: list of { x, y, z, doses }, nearest first,
-- and the litres of a dose.
function Plants:thirsty(part)
    local radius, dose = self.catalog:first(part, "spray", self.ctx)
    local out = {}
    if not radius then return out, 0 end
    for dx = -radius, radius do
        for dy = -radius, radius do
            local d2 = dx * dx + dy * dy
            if d2 <= radius * radius then
                local x, y = part.x + dx, part.y + dy
                local doses = Plants.dosesFor(self.farming:plant(x, y, part.z))
                if doses > 0 then out[#out + 1] = { x = x, y = y, z = part.z, doses = doses, d2 = d2 } end
            end
        end
    end
    table.sort(out, function(a, b)
        if a.d2 ~= b.d2 then return a.d2 < b.d2 end
        if a.x ~= b.x then return a.x < b.x end
        return a.y < b.y
    end)
    return out, dose
end

function Plants:need(part)
    local list, dose = self:thirsty(part)
    local doses = 0
    for i = 1, #list do doses = doses + list[i].doses end
    return doses * dose
end

function Plants:deliver(part, litres)
    local list, dose = self:thirsty(part)
    if dose <= 0 then return end
    local left = math.floor(litres / dose + EPSILON)
    for i = 1, #list do
        if left <= 0 then return end
        local n = math.min(left, list[i].doses)
        self.farming:water(list[i].x, list[i].y, list[i].z, n)
        left = left - n
    end
end

return Plants
