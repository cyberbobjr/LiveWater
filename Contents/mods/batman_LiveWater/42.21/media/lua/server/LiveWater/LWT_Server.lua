if isClient() then return end
-- LiveWater: composition root on the authority (solo game or server). Builds the services with
-- their game adapters at OnInitGlobalModData (the global ModData is reloaded just before it:
-- never keep a table of an earlier game) and wires the game events, each once:
--   OnObjectAdded / OnObjectAboutToBeRemoved  -> LWT_Placement (and a barrel connected, taken away
--                                                or set down again: LWT_HouseBarrels, L12)
--   OnClientCommand (module LiveWater)        -> LWT_Commands
--   EveryTenMinutes                           -> LWT_Clock (the only clock, ADR-001 D09)
--   OnInitWorld                               -> LWT_Power:register (Live Wire consumers, D20)
--   LiveWater.Events partAdded / partRemoved  -> LWT_Publisher (sprite by state, mirrored state)
--   LiveWater.Events waterDelivered / partRemoved -> LWT_Outlets (relay tanks of the house inlets,
--                                                plants of the sprinklers: LWT_Plants, barrels of
--                                                the fittings set to Fill: LWT_Fittings)
--   LiveWater.Events waterDrawn                   -> LWT_Fittings (barrels set to Pump)
-- No per-frame event (D08). Events before the first OnInitGlobalModData are ignored.
-- LiveWater.Server holds the services of the current game (nil before), for later adapters.

require "LiveWater/LWT_API"
local Protocol = require "LiveWater/LWT_Protocol"
local Registry = require "LiveWater/LWT_Registry"
local Network = require "LiveWater/LWT_Network"
local Flow = require "LiveWater/LWT_Flow"
local Sprites = require "LiveWater/LWT_Sprites"
local Topology = require "LiveWater/LWT_Topology"
local Placement = require "LiveWater/LWT_Placement"
local Clock = require "LiveWater/LWT_Clock"
local Commands = require "LiveWater/LWT_Commands"
local GameWorld = require "LiveWater/LWT_GameWorld"
local GamePlayers = require "LiveWater/LWT_GamePlayers"
local GameSettings = require "LiveWater/LWT_GameSettings"
local GameSounds = require "LiveWater/LWT_GameSounds"
local Power = require "LiveWater/LWT_Power"
local Publisher = require "LiveWater/LWT_Publisher"
local Outlets = require "LiveWater/LWT_Outlets"
local Relays = require "LiveWater/LWT_Relays"
local GamePlumbing = require "LiveWater/LWT_GamePlumbing"
local HouseBarrels = require "LiveWater/LWT_HouseBarrels"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local Diagnostics = require "LiveWater/LWT_Diagnostics"
local WasherFix = require "LiveWater/LWT_WasherFix"
local Plants = require "LiveWater/LWT_Plants"
local GameFarming = require "LiveWater/LWT_GameFarming"
local GameVisuals = require "LiveWater/LWT_GameVisuals"
local Broadcast = require "LiveWater/LWT_GameBroadcast"
local Fittings = require "LiveWater/LWT_Fittings"
local GameContainers = require "LiveWater/LWT_GameContainers"
local Checks = require "LiveWater/Commands/LWT_CmdChecks"
local Reasons = require "LiveWater/LWT_Reasons"

-- Command name -> handler file under LiveWater/Commands.
local COMMANDS = {
    [Protocol.LAY] = "LWT_CmdLay",
    [Protocol.DISMANTLE] = "LWT_CmdDismantle",
    [Protocol.FIT_FILTER] = "LWT_CmdFitFilter",
    [Protocol.REMOVE_FILTER] = "LWT_CmdRemoveFilter",
    [Protocol.SWITCH_PUMP] = "LWT_CmdSwitchPump",
    [Protocol.REPAIR_PUMP] = "LWT_CmdRepairPump",
    [Protocol.CONNECT_BARREL] = "LWT_CmdConnectBarrel",
    [Protocol.DISCONNECT_BARREL] = "LWT_CmdDisconnectBarrel",
    [Protocol.RESERVE_BARREL] = "LWT_CmdReserveBarrel",
    [Protocol.CITY_WATER] = "LWT_CmdCityWater",
    [Protocol.SWITCH_VALVE] = "LWT_CmdSwitchValve",
    [Protocol.SET_TIMER] = "LWT_CmdSetTimer",
    [Protocol.SHOW_NETWORK] = "LWT_CmdShowNetwork",
    [Protocol.SWITCH_FITTING] = "LWT_CmdSwitchFitting",
}

local MODDATA_KEY = "LiveWater"

local function log(message)
    print(message)
end

-- Stateless game adapters, needed before OnInitGlobalModData (Live Wire registration).
local world = GameWorld.new(LiveWater.Parts, LiveWater.Sources)
local power = Power.new({ catalog = LiveWater.Parts, world = world })

local function randomShare()
    return ZombRandFloat(0, 1)
end

local function gameHours()
    return getGameTime():getWorldAgeHours()
end

-- A part that pressurizes (a pump) is in the network of `part` (lifts the gravity rule, D28).
local function hasPump(network, catalog, part)
    local id = network:networkAt(part.x, part.y, part.z)
    local members = id and network:members(id) or {}
    for i = 1, #members do
        if catalog:any(members[i], "pressurizes") then return true end
    end
    return false
end

-- Replies of the commands to one player (network view).
local replies = { to = function(_, player, command, args) Broadcast.to(player, command, args) end }

-- A part set down that the network refuses: the players near are told why (D14).
local function notifier(players)
    return function(x, y, z, reason)
        local list = players:all()
        for i = 1, #list do
            if Checks.near(players, list[i], x, y, z) then players:tell(list[i], Reasons.key(reason)) end
        end
    end
end

local function build()
    local catalog = LiveWater.Parts
    local players = GamePlayers.new()
    local store = ModData.getOrCreate(MODDATA_KEY)
    local registry = Registry.new(store, catalog)
    local network = Network.new(catalog)
    local sprites = Sprites.new(network, catalog, world)
    local topology = Topology.new({ registry = registry, network = network, catalog = catalog,
        events = LiveWater.Events, sprites = sprites, sites = world, log = log })
    local publisher = Publisher.new({ catalog = catalog, sprites = sprites, mirror = world, sounds = GameSounds.new(),
        visuals = GameVisuals.new() })
    local plumbing = GamePlumbing.new()
    local relays = Relays.new({ store = store, plumbing = plumbing, world = world, now = gameHours,
        setting = GameSettings.scale, catalog = catalog, registry = registry, log = log })
    local outlets = Outlets.new(catalog)
    outlets:register("houseInlet", relays)
    outlets:register("sprinkler", Plants.new({ catalog = catalog, farming = GameFarming.new(), scale = GameSettings.scale }))
    local fittings = Fittings.new({ catalog = catalog, registry = registry, world = world,
        containers = GameContainers.new(), shapes = LiveWater.Containers, publisher = publisher })
    outlets:register("barrelFill", fittings)
    local function pumped(part) return hasPump(network, catalog, part) end
    local barrels = HouseBarrels.new({ store = store, plumbing = plumbing, world = world, relays = relays,
        lifted = pumped })
    local diagnostics = Diagnostics.new({ relays = relays, barrels = barrels, pumped = pumped })
    local washerFix = WasherFix.new({ relays = relays, plumbing = plumbing, multiplayer = isServer,
        enabled = function() return GameSettings.scale("WasherFix") ~= false end })
    local commands = Commands.new({ topology = topology, catalog = catalog, world = world,
        players = players, publisher = publisher, scale = GameSettings.scale, barrels = barrels,
        plumbing = plumbing, events = LiveWater.Events, replies = replies })
    for name, file in pairs(COMMANDS) do
        commands:register(name, require("LiveWater/Commands/" .. file))
    end
    local server = {
        registry = registry, network = network, topology = topology, commands = commands,
        publisher = publisher, power = power, outlets = outlets, relays = relays, barrels = barrels,
        fittings = fittings,
        placement = Placement.new(topology, catalog, log, world, notifier(players)),
        clock = Clock.new({ network = network, flow = Flow.new(catalog), catalog = catalog, world = world,
            events = LiveWater.Events, power = power, publisher = publisher, scale = GameSettings.scale,
            random = randomShare, hours = gameHours, sources = LiveWater.Sources, chores = { relays, barrels, diagnostics, washerFix, fittings },
            need = function(part) return outlets:need(part) end }),
    }
    local count = topology:rebuild()
    log("LiveWater: " .. count .. " part(s) loaded")
    return server
end

local function onInit()
    LiveWater.Server = build()
end

-- Sprite name and square of a game object, or nil.
local function whereIs(obj)
    local sq = obj and obj:getSquare()
    local name = obj and obj:getSpriteName()
    if not sq or not name then return nil end
    return name, sq:getX(), sq:getY(), sq:getZ()
end

local function onObjectAdded(obj)
    local server = LiveWater.Server
    if not server then return end
    local name, x, y, z = whereIs(obj)
    if not name then return end
    server.placement:added(name, x, y, z)
    if WaterObjects.mark(obj, WaterObjects.BARREL_KEY) then server.barrels:placed(x, y, z) end
    if WaterObjects.mark(obj, WaterObjects.WASHER_KEY) then
        -- a washer set down again is not plumbed any more (L12)
        obj:getModData()[WaterObjects.WASHER_KEY] = nil
        if isServer() then obj:transmitModData() end
    end
end

local function onObjectAboutToBeRemoved(obj)
    local server = LiveWater.Server
    if not server then return end
    local name, x, y, z = whereIs(obj)
    if not name then return end
    server.placement:removed(name, x, y, z)
    if WaterObjects.mark(obj, WaterObjects.BARREL_KEY) then server.barrels:disconnect(x, y, z) end
end

local function onClientCommand(module, command, player, args)
    local server = LiveWater.Server
    if module ~= Protocol.MODULE or not server or not player then return end
    server.commands:dispatch(player, command, args)
end

local function onInitWorld()
    local api = LiveWire and LiveWire.API
    local count = power:register(api)
    if count > 0 then log("LiveWater: " .. count .. " part type(s) registered as Live Wire consumers") end
end

local function onPartAdded(entry)
    local server = LiveWater.Server
    if server then server.publisher:present(entry) end
end

local function onPartRemoved(entry)
    local server = LiveWater.Server
    if not server then return end
    server.publisher:forget(entry)
    server.outlets:release(entry)
    server.barrels:forget(entry)
end

local function onWaterDelivered(part, litres, quality)
    local server = LiveWater.Server
    if server then server.outlets:deliver(part, litres, quality) end
end

local function onWaterDrawn(part, litres)
    local server = LiveWater.Server
    if server then server.fittings:drawn(part, litres) end
end

local function onTenMinutes()
    local server = LiveWater.Server
    if server then server.clock:tick() end
end

Events.OnInitWorld.Add(onInitWorld)
Events.OnInitGlobalModData.Add(onInit)
LiveWater.Events.on("partAdded", onPartAdded)
LiveWater.Events.on("partRemoved", onPartRemoved)
LiveWater.Events.on("waterDelivered", onWaterDelivered)
LiveWater.Events.on("waterDrawn", onWaterDrawn)
Events.OnObjectAdded.Add(onObjectAdded)
Events.OnObjectAboutToBeRemoved.Add(onObjectAboutToBeRemoved)
Events.OnClientCommand.Add(onClientCommand)
Events.EveryTenMinutes.Add(onTenMinutes)

return LiveWater
