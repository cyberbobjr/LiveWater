if isClient() then return end
-- LiveWater: the sound of a valve opened or closed by hand (ADR-008 D10), on the authority. Subscriber
-- of the event valveChanged (part, open); the players near hear it once (sounds port, LWT_GameSounds:
-- once). The two sounds are declared in media/scripts/LWT_sounds.txt, two takes each.

local ValveSounds = {}
ValveSounds.__index = ValveSounds

ValveSounds.OPEN = "LWT_ValveOpen"
ValveSounds.CLOSE = "LWT_ValveClose"

function ValveSounds.new(sounds)
    return setmetatable({ sounds = sounds }, ValveSounds)
end

function ValveSounds:changed(part, open)
    self.sounds:once(part.x, part.y, part.z, open and ValveSounds.OPEN or ValveSounds.CLOSE)
end

return ValveSounds
