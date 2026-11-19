-- LiveWater: who may remove LiveWater from the world (ADR-016). In multiplayer, client or server: the admin
-- role (capability UseDebugContextMenu, vanilla ClientCommands.lua). In solo: only a game started in debug
-- mode (-debug launch option). The client menu shows the option with it, the authority checks it again.

local RemovalRight = {}

function RemovalRight.allowed(player)
    if isClient() or isServer() then
        return player:getRole():hasCapability(Capability.UseDebugContextMenu) == true
    end
    return isDebugEnabled() == true
end

return RemovalRight
