-- LiveWater: game adapter of a place a part may stand on (the `site` of Parts:attach). Both
-- sides: the furniture cursor asks it on the client, the authority when the part joins.
-- It looks at the 8 squares around (x, y, z), never further:
--   hasFlag(name)    one of them carries IsoFlagType[name]
--   hasSprite(name)  one of them holds an object with that sprite
--   source()         kind of the water source found around (LWT_Sources), or nil
--   hasVessel()      one of the 4 squares on its sides (not the corners) holds a barrel the fittings
--                    work with (LWT_WaterObjects.isBarrel), API revision 21, ADR-011 D01, or a gas
--                    station fuel pump (LWT_WaterObjects.isFuelPump), API revision 23, ADR-014 D01
-- barrels (optional): { registry (LWT_Containers), listed = function() -> set of the names of the
-- sandbox option FillContainers }; without it the site holds no barrel.

local WaterObjects = require "LiveWater/LWT_WaterObjects"

local GameSite = {}
GameSite.__index = GameSite

-- Offsets of the 4 squares on the sides.
local SIDES = { { 0, -1 }, { 1, 0 }, { 0, 1 }, { -1, 0 } }

function GameSite.new(sources, x, y, z, barrels)
    return setmetatable({ sources = sources, x = x, y = y, z = z, barrels = barrels }, GameSite)
end

function GameSite:neighbours()
    if self.squares then return self.squares end
    local list, cell = {}, getCell()
    for dx = -1, 1 do
        for dy = -1, 1 do
            if dx ~= 0 or dy ~= 0 then
                local sq = cell and cell:getGridSquare(self.x + dx, self.y + dy, self.z)
                if sq then list[#list + 1] = sq end
            end
        end
    end
    self.squares = list
    return list
end

function GameSite:hasFlag(name)
    local flag = IsoFlagType[name]
    if flag == nil then return false end
    local list = self:neighbours()
    for i = 1, #list do
        if list[i]:has(flag) then return true end
    end
    return false
end

function GameSite:hasSprite(name)
    if not self.spriteSet then
        local set, list = {}, self:neighbours()
        for i = 1, #list do
            local objects = list[i]:getObjects()
            for j = 0, objects:size() - 1 do
                local s = objects:get(j):getSpriteName()
                if s then set[s] = true end
            end
        end
        self.spriteSet = set
    end
    return self.spriteSet[name] == true
end

function GameSite:source()
    return self.sources:find(self)
end

local function holdsBarrel(square, registry, listed)
    local objects = square:getObjects()
    for j = 0, objects:size() - 1 do
        local obj = objects:get(j)
        if WaterObjects.isBarrel(obj, registry, listed) or WaterObjects.isFuelPump(obj) then return true end
    end
    return false
end

function GameSite:findVessel()
    if not self.barrels then return false end
    local cell, registry, listed = getCell(), self.barrels.registry, self.barrels.listed()
    for i = 1, #SIDES do
        local sq = cell and cell:getGridSquare(self.x + SIDES[i][1], self.y + SIDES[i][2], self.z)
        if sq and holdsBarrel(sq, registry, listed) then return true end
    end
    return false
end

function GameSite:hasVessel()
    if self.vessel == nil then self.vessel = self:findVessel() end
    return self.vessel
end

return GameSite
