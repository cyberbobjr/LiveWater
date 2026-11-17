-- LiveWater: game adapter of a place a part may stand on (the `site` of Parts:attach). Both
-- sides: the furniture cursor asks it on the client, the authority when the part joins.
-- It looks at the 8 squares around (x, y, z), never further:
--   hasFlag(name)    one of them carries IsoFlagType[name]
--   hasSprite(name)  one of them holds an object with that sprite
--   source()         kind of the water source found around (LWT_Sources), or nil

local GameSite = {}
GameSite.__index = GameSite

function GameSite.new(sources, x, y, z)
    return setmetatable({ sources = sources, x = x, y = y, z = z }, GameSite)
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

return GameSite
