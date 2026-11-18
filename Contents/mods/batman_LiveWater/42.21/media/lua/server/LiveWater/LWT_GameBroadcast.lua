if isClient() then return end
-- LiveWater: game adapter that sends a server command of the module LiveWater to the clients,
-- authority only. On a server: sendServerCommand; in solo sendServerCommand does nothing, so the
-- client handlers run through the same OnServerCommand event (triggerEvent).
--   all(command, args)            every client
--   to(player, command, args)     one player's client

local Protocol = require "LiveWater/LWT_Protocol"

local Broadcast = {}

function Broadcast.all(command, args)
    if isServer() then
        sendServerCommand(Protocol.MODULE, command, args)
    else
        triggerEvent("OnServerCommand", Protocol.MODULE, command, args)
    end
end

function Broadcast.to(player, command, args)
    if isServer() then
        sendServerCommand(player, Protocol.MODULE, command, args)
    else
        triggerEvent("OnServerCommand", Protocol.MODULE, command, args)
    end
end

return Broadcast
