if isClient() then return end
-- LiveWater: game adapter of the sounds port (P15), authority only.
--   loop(x, y, z, name)               tell the players to play the loop `name` at the part, or to
--                                     stop it (name nil): sendServerCommand to every client on a
--                                     server; in solo the client handler runs through the same
--                                     OnServerCommand event (sendServerCommand does nothing there)
--   noise(x, y, z, radius, volume)    world sound zombies hear (addSound, no source object)

local Protocol = require "LiveWater/LWT_Protocol"

local GameSounds = {}
GameSounds.__index = GameSounds

function GameSounds.new()
    return setmetatable({}, GameSounds)
end

function GameSounds:loop(x, y, z, name)
    local args = { x = x, y = y, z = z, name = name }
    if isServer() then
        sendServerCommand(Protocol.MODULE, Protocol.SOUND, args)
    else
        triggerEvent("OnServerCommand", Protocol.MODULE, Protocol.SOUND, args)
    end
end

function GameSounds:noise(x, y, z, radius, volume)
    if radius > 0 and volume > 0 then addSound(nil, x, y, z, radius, volume) end
end

return GameSounds
