-- LiveWater: timed action of the LiveWater menus (ADR-001 E13): the player walks next to the square
-- (luautils.walkAdj), faces it, works for a moment, then the command is sent to the authority, which
-- checks everything again (LWT_Commands). Client only: the class has no `complete`, so the engine
-- does not ask the server to run it (LuaTimedActionNew: no complete = custom remote sync, Java 42.22);
-- the command is the network part. No per-frame event: the action's own update is the vanilla one.
--   LWT_PartAction.queue(player, sq, command, extra, time)   walk there, then act (time in action
--                                                            ticks, DEFAULT_TIME when nil)

require "TimedActions/ISBaseTimedAction"
local Protocol = require "LiveWater/LWT_Protocol"

LWT_PartAction = ISBaseTimedAction:derive("LWT_PartAction")

LWT_PartAction.DEFAULT_TIME = 60

-- Arguments of the command about a square: { x, y, z } plus `extra`.
function LWT_PartAction.args(sq, extra)
    local args = { x = sq:getX(), y = sq:getY(), z = sq:getZ() }
    for k, v in pairs(extra or {}) do args[k] = v end
    return args
end

function LWT_PartAction:isValid()
    return self.sq ~= nil and self.character ~= nil
end

function LWT_PartAction:waitToStart()
    self.character:faceLocation(self.sq:getX(), self.sq:getY())
    return self.character:shouldBeTurning()
end

function LWT_PartAction:start()
    self:setActionAnim("Loot")
    self.character:SetVariable("LootPosition", "Low")
end

function LWT_PartAction:perform()
    sendClientCommand(self.character, Protocol.MODULE, self.command, LWT_PartAction.args(self.sq, self.extra))
    ISBaseTimedAction.perform(self)
end

function LWT_PartAction:new(character, sq, command, extra, time)
    local o = ISBaseTimedAction.new(self, character)
    o.sq = sq
    o.command = command
    o.extra = extra
    o.maxTime = time or LWT_PartAction.DEFAULT_TIME
    return o
end

function LWT_PartAction.queue(player, sq, command, extra, time)
    luautils.walkAdj(player, sq, true)
    ISTimedActionQueue.add(LWT_PartAction:new(player, sq, command, extra, time))
end

return LWT_PartAction
