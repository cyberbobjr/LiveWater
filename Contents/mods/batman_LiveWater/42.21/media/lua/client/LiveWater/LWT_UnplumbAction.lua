-- LiveWater: timed action of "Unplumb" (ADR-024 D04), client. An LWT_PartAction (the command
-- "unplumb" is sent to the authority when the work is done) with the tool, time and sound of the
-- game's own plumbing action (ISPlumbItem: wrench equipped, 100 ticks, RepairWithWrench).

require "LiveWater/LWT_PartAction"
local Protocol = require "LiveWater/LWT_Protocol"

LWT_UnplumbAction = LWT_PartAction:derive("LWT_UnplumbAction")

LWT_UnplumbAction.TIME = 100

function LWT_UnplumbAction:isValid()
    return LWT_PartAction.isValid(self) and self.character:isEquipped(self.wrench)
end

function LWT_UnplumbAction:start()
    self.sound = self.character:playSound("RepairWithWrench")
end

function LWT_UnplumbAction:stop()
    self.character:stopOrTriggerSound(self.sound)
    ISBaseTimedAction.stop(self)
end

function LWT_UnplumbAction:perform()
    self.character:stopOrTriggerSound(self.sound)
    LWT_PartAction.perform(self)
end

function LWT_UnplumbAction:new(character, sq, wrench)
    local time = character:isTimedActionInstant() and 1 or LWT_UnplumbAction.TIME
    local o = LWT_PartAction.new(self, character, sq, Protocol.UNPLUMB, nil, time)
    o.wrench = wrench
    return o
end

return LWT_UnplumbAction
