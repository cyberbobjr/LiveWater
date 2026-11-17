-- LiveWater: sound loops of the parts that run (pond pump, P15), played locally by each client
-- when the authority says so (server command "sound" { x, y, z, name }; name nil = stop). One
-- free emitter per square, started once (the authority repeats the order every ten minutes for
-- the players who came near since), stopped on order. No per-frame code: nothing runs between
-- two orders. playSoundImpl(name, false, nil) on a free emitter plays locally, no packet.

local Protocol = require "LiveWater/LWT_Protocol"

local PumpSounds = { playing = {} }

local function isCoordinate(v)
    return type(v) == "number" and v == v and v % 1 == 0
end

local function stop(key)
    local current = PumpSounds.playing[key]
    if current then
        current.emitter:stopSound(current.id)
        PumpSounds.playing[key] = nil
    end
end

function PumpSounds.onServerCommand(module, command, args)
    if module ~= Protocol.MODULE or command ~= Protocol.SOUND or type(args) ~= "table" then return end
    local x, y, z = args.x, args.y, args.z
    if not (isCoordinate(x) and isCoordinate(y) and isCoordinate(z)) then return end
    local key = x .. "," .. y .. "," .. z
    local name = args.name
    if type(name) ~= "string" then
        stop(key)
        return
    end
    local current = PumpSounds.playing[key]
    if current and current.name == name and current.emitter:isPlaying(current.id) then return end
    stop(key)
    local emitter = getWorld():getFreeEmitter(x + 0.5, y + 0.5, z)
    local id = emitter:playSoundImpl(name, false, nil)
    PumpSounds.playing[key] = { emitter = emitter, id = id, name = name }
end

Events.OnServerCommand.Add(PumpSounds.onServerCommand)

return PumpSounds
