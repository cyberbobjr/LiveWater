-- LiveWater: animated water jet of the sprinklers, client only (ADR-001 D08a, P14). The ONLY per-frame
-- subscription of LiveWater, allowed by D08a and by tools/check_mod.py for this file alone:
--   * Events.OnTick is subscribed only while at least one sprinkler that sprays is loaded around the
--     local player (its square was loaded on this client), once, and removed as soon as none is left;
--   * the jet frame changes at most 6 times per real second (getTimestampMs), no game work: no data
--     written, no command sent;
--   * the frame is an attached sprite of the tileset (jet frames of the part's `spray` capability,
--     tuiles-contrat.md: 80 + 4 * frame + facing), and the object is marked animating while it runs
--     (the B42 chunk render cache only redraws an object every frame when isAnimating(),
--     FBORenderCell.java, knowledge base "Calque anime (AttachAnim)"); stopped: frame removed,
--     animating false.
-- Candidates are tracked without scanning squares every frame: LoadGridsquare and OnObjectAdded read
-- the part's mirrored state (LWT_Mirror), ReuseGridsquare drops the square, and the server command
-- "jet" { x, y, z } (LWT_Publisher, when a sprinkler starts or stops) reads the square again. A
-- received UpdateItemSprite clears attached sprites: the loop attaches the frame again at its next
-- swap. Client option (Mod options, "Animated sprinkler jet"): off shows a still jet, without OnTick.
-- Never runs on a dedicated server (client files are not loaded there; guard below).

if isServer() then return end

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local Mirror = require "LiveWater/LWT_Mirror"
local Grid = require "LiveWater/LWT_Grid"

local Jet = { running = {}, count = 0, ticking = false, animated = true, last = 0, frame = 0, swaps = 0 }

-- Milliseconds between two frames: at most 6 per second.
Jet.INTERVAL = 167
Jet.FACINGS = 4

local function eachObject(sq, fn)
    local objects = sq:getObjects()
    for i = 0, objects:size() - 1 do fn(objects:get(i)) end
end

-- Jet of a part object (nil when it has none) and whether it sprays, from its mirrored state.
local function jetOf(obj)
    local name = obj:getSpriteName()
    local catalog = LiveWater.Parts
    local id = name and catalog:typeOfSprite(name)
    if not id then return nil end
    local state = Mirror.read(obj)
    local part = { type = id, data = state and state.type == id and state.data or {} }
    local sheet, first, frames, on = catalog:first(part, "jet")
    if not sheet then return nil end
    local e = { id = id, sheet = sheet, first = first, frames = frames, facing = (catalog:facingOf(name) or 1) - 1,
        names = {} }
    for f = 0, frames - 1 do
        for k = 0, Jet.FACINGS - 1 do e.names[sheet .. (first + Jet.FACINGS * f + k)] = true end
    end
    return e, on == true
end

-- Remove the jet frames attached to the object (only ours).
local function strip(obj, e)
    local list = obj:getAttachedAnimSprite()
    if not list then return end
    for i = list:size() - 1, 0, -1 do
        local sprite = list:get(i):getParentSprite()
        local name = sprite and sprite:getName()
        if name and e.names[name] then obj:RemoveAttachedAnim(i) end
    end
end

local function show(obj, e, frame)
    strip(obj, e)
    obj:addAttachedAnimSpriteByName(e.sheet .. (e.first + Jet.FACINGS * (frame % e.frames) + e.facing))
    obj:setAnimating(Jet.animated)
end

local function clear(obj, e)
    strip(obj, e)
    obj:setAnimating(false)
end

-- The part object of the entry on its square, or nil (square unloaded, object gone).
local function objectOf(e)
    local sq = getCell():getGridSquare(e.x, e.y, e.z)
    if not sq then return nil end
    local found = nil
    eachObject(sq, function(obj)
        local name = obj:getSpriteName()
        if not found and name and LiveWater.Parts:typeOfSprite(name) == e.id then found = obj end
    end)
    return found
end

function Jet.subscribe()
    local want = Jet.count > 0 and Jet.animated
    if want and not Jet.ticking then
        Events.OnTick.Add(Jet.tick)
        Jet.ticking = true
    elseif not want and Jet.ticking then
        Events.OnTick.Remove(Jet.tick)
        Jet.ticking = false
    end
end

local function forget(key)
    if Jet.running[key] then
        Jet.running[key] = nil
        Jet.count = Jet.count - 1
    end
end

local function start(key, obj, e)
    if not Jet.running[key] then Jet.count = Jet.count + 1 end
    Jet.running[key] = e
    show(obj, e, Jet.animated and Jet.frame or 0)
end

local function stop(key, obj, e)
    clear(obj, e)
    forget(key)
end

-- Read a square again: its sprinklers that spray run, the others stop.
function Jet.watch(sq)
    local x, y, z = sq:getX(), sq:getY(), sq:getZ()
    local key, seen = Grid.key(x, y, z), false
    eachObject(sq, function(obj)
        local e, on = jetOf(obj)
        if not e then return end
        seen = true
        e.x, e.y, e.z = x, y, z
        if on then start(key, obj, e) else stop(key, obj, e) end
    end)
    if not seen then forget(key) end
    Jet.subscribe()
end

function Jet.tick()
    local now = getTimestampMs()
    if now - Jet.last < Jet.INTERVAL then return end
    Jet.last = now
    Jet.frame = Jet.frame + 1
    Jet.swaps = Jet.swaps + 1
    for key, e in pairs(Jet.running) do
        local obj = objectOf(e)
        if obj then show(obj, e, Jet.frame) else forget(key) end
    end
    Jet.subscribe()
end

-- Animated jet (true) or still jet (false): client option.
function Jet.setAnimated(on)
    Jet.animated = on ~= false
    for key, e in pairs(Jet.running) do
        local obj = objectOf(e)
        if obj then show(obj, e, Jet.animated and Jet.frame or 0) else forget(key) end
    end
    Jet.subscribe()
end

function Jet.onLoadGridsquare(sq)
    Jet.watch(sq)
end

function Jet.onReuseGridsquare(sq)
    if Jet.count == 0 then return end
    forget(Grid.key(sq:getX(), sq:getY(), sq:getZ()))
    Jet.subscribe()
end

function Jet.onObjectAdded(obj)
    local sq = obj and obj:getSquare()
    if sq then Jet.watch(sq) end
end

local function isCoordinate(v)
    return type(v) == "number" and v == v and v % 1 == 0
end

function Jet.onServerCommand(module, command, args)
    if module ~= Protocol.MODULE or command ~= Protocol.JET or type(args) ~= "table" then return end
    if not (isCoordinate(args.x) and isCoordinate(args.y) and isCoordinate(args.z)) then return end
    local sq = getCell():getGridSquare(args.x, args.y, args.z)
    if sq then Jet.watch(sq) end
end

-- Mod options (PZAPI.ModOptions, vanilla 42.22): "Animated sprinkler jet", on by default.
local function setupOptions()
    if not (PZAPI and PZAPI.ModOptions) then return end
    local options = PZAPI.ModOptions:create("batman_LiveWater", "UI_LWT_Options")
    local tick = options:addTickBox("animatedJet", "UI_LWT_AnimatedJet", true, "UI_LWT_AnimatedJet_Tooltip")
    options.apply = function() Jet.setAnimated(tick:getValue()) end
    Events.OnGameStart.Add(function() Jet.setAnimated(tick:getValue()) end)
end

setupOptions()
Events.LoadGridsquare.Add(Jet.onLoadGridsquare)
Events.ReuseGridsquare.Add(Jet.onReuseGridsquare)
Events.OnObjectAdded.Add(Jet.onObjectAdded)
Events.OnServerCommand.Add(Jet.onServerCommand)

return Jet
