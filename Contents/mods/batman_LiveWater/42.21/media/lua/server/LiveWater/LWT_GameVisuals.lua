if isClient() then return end
-- LiveWater: game adapter of the visuals port of LWT_Publisher, authority only.
--   jet(x, y, z)   tell the clients that the sprinkler there started or stopped spraying (server
--                  command "jet"): each client reads its mirrored state again (LWT_SprinklerJet)

local Protocol = require "LiveWater/LWT_Protocol"
local Broadcast = require "LiveWater/LWT_GameBroadcast"

local GameVisuals = {}
GameVisuals.__index = GameVisuals

function GameVisuals.new()
    return setmetatable({}, GameVisuals)
end

function GameVisuals:jet(x, y, z)
    Broadcast.all(Protocol.JET, { x = x, y = y, z = z })
end

return GameVisuals
