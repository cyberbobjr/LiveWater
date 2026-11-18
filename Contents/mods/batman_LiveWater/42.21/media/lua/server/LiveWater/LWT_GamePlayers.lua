if isClient() then return end
-- LiveWater: game adapter of the players port, authority only (the server's copy of the
-- inventory is the one that counts; changes are sent to the owner).
--   position(player)          x, y, z
--   has(player, fullType)     item of that full type in the inventory (bags included)
--   count(player, fullType)   how many (bags included)
--   take(player, fullType)    remove one: true and the share of it left (condition / max,
--                             1 for an item without condition), or false
--   give(player, fullType, share)  add one (dropped at the feet when too heavy); `share`
--                             (optional, 0..1) sets its condition
--   hasTool(player, tag)      item with that tag ("base:pipewrench") in the inventory
--   tell(player, key)         show a translated note: sent to the client on a server, shown
--                             directly in solo (sendServerCommand does nothing in solo)
--   isAdmin(player)           may remove LiveWater from the world: role capability
--                             UseDebugContextMenu on a server (vanilla ClientCommands.lua), always in solo
--   all()                     the players of the game (online players on a server, local ones
--                             in solo)

local Notice = require "LiveWater/LWT_Notice"
local Protocol = require "LiveWater/LWT_Protocol"

local GamePlayers = {}
GamePlayers.__index = GamePlayers

function GamePlayers.new()
    return setmetatable({}, GamePlayers)
end

function GamePlayers:position(player)
    return player:getX(), player:getY(), player:getZ()
end

function GamePlayers:has(player, fullType)
    return player:getInventory():containsTypeRecurse(fullType)
end

local function shareOf(item)
    local max = item:getConditionMax()
    if not max or max <= 0 then return 1 end
    return item:getCondition() / max
end

function GamePlayers:count(player, fullType)
    return player:getInventory():getCountTypeRecurse(fullType)
end

function GamePlayers:take(player, fullType)
    local item = player:getInventory():getFirstTypeRecurse(fullType)
    if not item then return false end
    local share = shareOf(item)
    local container = item:getContainer()
    container:Remove(item)
    sendRemoveItemFromContainer(container, item)
    return true, share
end

function GamePlayers:give(player, fullType, share)
    local item = instanceItem(fullType)
    if not item then return false end
    local max = item:getConditionMax()
    if share and max and max > 0 then item:setCondition(math.max(1, math.floor(share * max + 0.5))) end
    Actions.addOrDropItem(player, item)
    return true
end

function GamePlayers:hasTool(player, tag)
    local itemTag = ItemTag.get(ResourceLocation.of(tag))
    return itemTag ~= nil and player:getInventory():containsTagRecurse(itemTag)
end

function GamePlayers:isAdmin(player)
    if not isServer() then return true end
    return player:getRole():hasCapability(Capability.UseDebugContextMenu)
end

function GamePlayers:all()
    local out = {}
    if isServer() then
        local list = getOnlinePlayers()
        for i = 0, list:size() - 1 do out[#out + 1] = list:get(i) end
    else
        for i = 0, getNumActivePlayers() - 1 do
            local p = getSpecificPlayer(i)
            if p then out[#out + 1] = p end
        end
    end
    return out
end

function GamePlayers:tell(player, key)
    if isServer() then
        sendServerCommand(player, Protocol.MODULE, Protocol.NOTICE, { key = key })
    else
        Notice.show(player, key)
    end
end

return GamePlayers
