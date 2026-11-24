if isClient() then return end
-- LiveWater: game adapter of the farming port (sprinklers, ADR-001 D19), authority only. Vanilla
-- farming (42.22, media/lua/server/Farming): SFarmingSystem.instance:getLuaObjectAt(x, y, z) gives the
-- plant (SPlantGlobalObject) or nil; SPlantGlobalObject:water(nil, uses) adds 10 per use, notes the
-- hour of the watering and saves (transmitModData). Thin: the rules are in LWT_Plants.
--   plant(x, y, z)          { alive, level = waterLvl, needed = waterNeeded, max = waterNeededMax } or nil
--   water(x, y, z, doses)   true when watered

local GameFarming = {}
GameFarming.__index = GameFarming

function GameFarming.new()
    return setmetatable({}, GameFarming)
end

local function plantAt(x, y, z)
    local system = SFarmingSystem and SFarmingSystem.instance
    return system and system:getLuaObjectAt(x, y, z) or nil
end

function GameFarming:plant(x, y, z)
    local p = plantAt(x, y, z)
    if not p then return nil end
    return { alive = p.state ~= "plow" and p:isAlive(), level = p.waterLvl or 0, needed = p.waterNeeded or 0,
        max = p.waterNeededMax }
end

function GameFarming:water(x, y, z, doses)
    local p = plantAt(x, y, z)
    if not p then return false end
    p:water(nil, doses)
    return true
end

return GameFarming
