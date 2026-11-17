if isClient() then return end
-- LiveWater: client commands on the authority. One dispatcher, a handler table by command
-- name (one file per command under LiveWater/Commands). A handler is
--   function(ctx, player, args) -> true, or false and a reason
-- and re-checks every argument: nothing the client sends is trusted. A refusal is told to the
-- player as a translation key (REASONS, else GENERIC), translated on the client side.
-- ctx = { topology, catalog, world, players } (ports: LWT_GameWorld, LWT_GamePlayers).

local Commands = {}
Commands.__index = Commands

local Reasons = require "LiveWater/LWT_Reasons"

-- Reason -> translation key told to the player (IG_UI.json, LWT_Reasons).
Commands.REASONS = Reasons.KEYS
Commands.GENERIC = Reasons.GENERIC

function Commands.new(ctx)
    return setmetatable({ ctx = ctx, handlers = {} }, Commands)
end

-- Returns true, or false and "duplicate_command" or "invalid_handler".
function Commands:register(name, handler)
    if type(handler) ~= "function" then return false, "invalid_handler" end
    if self.handlers[name] then return false, "duplicate_command" end
    self.handlers[name] = handler
    return true
end

-- Run the handler of `name`. Returns true, or false and the reason (told to the player).
function Commands:dispatch(player, name, args)
    local handler = self.handlers[name]
    if not handler then return false, "unknown_command" end
    local ok, reason = handler(self.ctx, player, args or {})
    if ok then return true end
    self.ctx.players:tell(player, Reasons.key(reason))
    return false, reason
end

return Commands
