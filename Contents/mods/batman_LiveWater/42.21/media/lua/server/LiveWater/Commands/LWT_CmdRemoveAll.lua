if isClient() then return end
-- LiveWater command "removeLiveWater" {}: an admin removes LiveWater from the world (P21, L14,
-- LWT_Removal). Checks: the player is an admin (players port: isAdmin). The player is told it started.

return function(ctx, player)
    if not ctx.players:isAdmin(player) then return false, "not_admin" end
    ctx.removal:start()
    ctx.players:tell(player, "IGUI_LWT_Removing")
    return true
end
