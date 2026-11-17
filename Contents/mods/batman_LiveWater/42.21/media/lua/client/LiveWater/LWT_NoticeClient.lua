-- LiveWater: shows on the client the notes the server sends (refusal of a command, translation
-- key). In solo the server code shows them itself (LWT_GamePlayers).

local Protocol = require "LiveWater/LWT_Protocol"
local Notice = require "LiveWater/LWT_Notice"

local function onServerCommand(module, command, args)
    if module ~= Protocol.MODULE or command ~= Protocol.NOTICE or type(args) ~= "table" then return end
    Notice.show(getPlayer(), args.key)
end

Events.OnServerCommand.Add(onServerCommand)
