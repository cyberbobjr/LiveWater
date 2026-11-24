if isClient() then return end
-- LiveWater: the plants an outlet waters, on the authority (ADR-001 D19, P13; ADR-004 D02; ADR-006
-- D01; ADR-027 D01). Handler of the outlet types "sprinkler" and "drip" (LWT_Outlets), one instance per type:
--   need(part)              its flow: the litres it draws per step, thirsty plants or not (ADR-006 D01)
--   deliver(part, litres)   the water that reaches the area (litres less the share lost in the air)
--                           fills the plants that are under their capacity, nearest first; the rest is lost
-- A plant is filled up to its capacity: its own waterNeededMax when the crop declares one, raised to its
-- stage need when that one is lower, never above 100; 100 when the crop declares none (ADR-027 D01). One
-- vanilla dose (SPlantGlobalObject:water) adds DOSE_POINTS and the game caps the level at 100, so a plant
-- needs ceil((capacity - level) / DOSE_POINTS) doses; a plant at 100 gets nothing. The squares watered, the
-- dose, the share lost and the flow come from an injected area strategy (sprinkler: LWT_SprayArea.reach, the
-- square of its radius; drip line: LWT_DripArea.reach, its unlinked neighbours, ADR-004 D02): one handler per
-- outlet type, the dose rules shared. No game API here; dependencies are injected: { farming (port:
-- plant(x, y, z) -> { alive, level, needed, max } or nil; water(x, y, z, doses)), area = function(part) ->
-- list of { x, y, d2 }, litres of a dose, share of the water drawn lost (0 when none), litres drawn per step }.

local Plants = {}
Plants.__index = Plants

Plants.DOSE_POINTS = 10
local MAX_LEVEL = 100
local EPSILON = 0.000001

function Plants.new(deps)
    return setmetatable({ farming = deps.farming, area = deps.area }, Plants)
end

-- Water level a plant is filled up to: its declared capacity (waterNeededMax), raised to its stage need when
-- that one is lower, never above the game's maximum; 100 when the crop declares none (ADR-027 D01).
function Plants.capacity(plant)
    local level = plant.max or 0
    if level <= 0 then return MAX_LEVEL end
    if level < (plant.needed or 0) then level = plant.needed or 0 end
    if level > MAX_LEVEL then level = MAX_LEVEL end
    return level
end

-- Doses a plant needs now to reach its capacity (0 when none).
function Plants.dosesFor(plant)
    if not plant or not plant.alive then return 0 end
    local missing = Plants.capacity(plant) - (plant.level or 0)
    if missing <= 0 then return 0 end
    return math.ceil(missing / Plants.DOSE_POINTS)
end

-- Plants of `area` (squares of the part) that need water: list of { x, y, z, doses }, nearest first.
function Plants:thirsty(part, area)
    local out = {}
    for i = 1, #area do
        local sq = area[i]
        local doses = Plants.dosesFor(self.farming:plant(sq.x, sq.y, part.z))
        if doses > 0 then out[#out + 1] = { x = sq.x, y = sq.y, z = part.z, doses = doses, d2 = sq.d2 } end
    end
    table.sort(out, function(a, b)
        if a.d2 ~= b.d2 then return a.d2 < b.d2 end
        if a.x ~= b.x then return a.x < b.x end
        return a.y < b.y
    end)
    return out
end

-- Litres the outlet draws this step: its flow (ADR-006 D01).
function Plants:need(part)
    local _, _, _, flow = self.area(part)
    return flow or 0
end

function Plants:deliver(part, litres)
    local area, dose, loss = self.area(part)
    if not dose or dose <= 0 then return end
    local left = math.floor(litres * (1 - (loss or 0)) / dose + EPSILON)
    if left <= 0 then return end
    local list = self:thirsty(part, area)
    for i = 1, #list do
        if left <= 0 then return end
        local n = math.min(left, list[i].doses)
        self.farming:water(list[i].x, list[i].y, list[i].z, n)
        left = left - n
    end
end

return Plants
