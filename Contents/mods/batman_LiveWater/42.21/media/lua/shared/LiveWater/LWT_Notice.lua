-- LiveWater: a short translated note above a player's head (refusal of a command). Shown where
-- the player's game runs: by the client on OnServerCommand (multiplayer), by the server code in
-- solo. The key must exist in Translate (keys "IGUI_LWT_*").

local Notice = {}

function Notice.show(player, key)
    if player and type(key) == "string" then
        player:setHaloNote(getText(key), 255, 200, 120, 300)
    end
end

return Notice
