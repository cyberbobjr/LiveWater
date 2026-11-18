if isClient() then return end
-- LiveWater: game adapter of the sounds port (P15), authority only.
--   loop(x, y, z, name)               tell the players to play the loop `name` at the part, or to
--                                     stop it (name nil): server command "sound" to every client
--                                     (LWT_GameBroadcast)
--   noise(x, y, z, radius, volume)    world sound zombies hear (addSound, no source object)

local Protocol = require "LiveWater/LWT_Protocol"
local Broadcast = require "LiveWater/LWT_GameBroadcast"

local GameSounds = {}
GameSounds.__index = GameSounds

function GameSounds.new()
    return setmetatable({}, GameSounds)
end

function GameSounds:loop(x, y, z, name)
    Broadcast.all(Protocol.SOUND, { x = x, y = y, z = z, name = name })
end

function GameSounds:noise(x, y, z, radius, volume)
    if radius > 0 and volume > 0 then addSound(nil, x, y, z, radius, volume) end
end

return GameSounds
