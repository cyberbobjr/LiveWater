if isClient() then return end
-- LiveWater: composition root on the authority (solo game or server). Builds the services with
-- their game adapters at OnInitGlobalModData (the global ModData is reloaded just before it:
-- never keep a table of an earlier game) and wires the game events, each once:
--   OnObjectAdded / OnObjectAboutToBeRemoved  -> LWT_Placement
--   OnObjectAdded / OnObjectAboutToBeRemoved of a fixture or a water tank, LoadChunk
--                                             -> LWT_Relays (fixtures surveyed again, D10)
--   LoadChunk                                 -> LWT_Fittings (count kept while away written
--                                                to the barrel), LWT_Publisher (parts stepped
--                                                while away show their state, ADR-006 D06)
--   OnClientCommand (module LiveWater)        -> LWT_Commands
--   EveryTenMinutes                           -> LWT_Clock (the only clock, ADR-001 D09)
--   OnInitWorld                               -> LWT_Power:register (Live Wire consumers, D20)
--   LiveWater.Events partAdded / partRemoved  -> LWT_Publisher (sprite by state, mirrored state)
--   LiveWater.Events waterDelivered / partRemoved -> LWT_Outlets (relay tanks of the house inlets,
--                                                plants of the sprinklers and the drip lines:
--                                                LWT_Plants with an area strategy, barrels of
--                                                the barrel fittings: LWT_Fittings)
--   LiveWater.Events waterDrawn                   -> LWT_Fittings (barrels pumps stand against)
--   LiveWater.Events networkChanged               -> LWT_Clock:settle (a network left without pump
--                                                stops showing water)
--   LiveWater.Events valveChanged                 -> LWT_ValveSounds, LWT_Clock:switched (the water
--                                                follows at once), LWT_Outlets:cut (ADR-010)
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
local ValveSounds = require "LiveWater/LWT_ValveSounds"
local Power = require "LiveWater/LWT_Power"
local Publisher = require "LiveWater/LWT_Publisher"
local Outlets = require "LiveWater/LWT_Outlets"
local Relays = require "LiveWater/LWT_Relays"
local GamePlumbing = require "LiveWater/LWT_GamePlumbing"
local WaterObjects = require "LiveWater/LWT_WaterObjects"
local Diagnostics = require "LiveWater/LWT_Diagnostics"
local WasherFix = require "LiveWater/LWT_WasherFix"
local Plants = require "LiveWater/LWT_Plants"
local SprayArea = require "LiveWater/LWT_SprayArea"
local DripArea = require "LiveWater/LWT_DripArea"
local GameFarming = require "LiveWater/LWT_GameFarming"
local GameVisuals = require "LiveWater/LWT_GameVisuals"
local Broadcast = require "LiveWater/LWT_GameBroadcast"
local Fittings = require "LiveWater/LWT_Fittings"
local GameContainers = require "LiveWater/LWT_GameContainers"
local Removal = require "LiveWater/LWT_Removal"
local Checks = require "LiveWater/Commands/LWT_CmdChecks"
local Reasons = require "LiveWater/LWT_Reasons"

-- Command name -> handler file under LiveWater/Commands.
local COMMANDS = {
    [Protocol.FIT_FILTER] = "LWT_CmdFitFilter",
    [Protocol.REMOVE_FILTER] = "LWT_CmdRemoveFilter",
    [Protocol.SWITCH_PUMP] = "LWT_CmdSwitchPump",
    [Protocol.REPAIR_PUMP] = "LWT_CmdRepairPump",
    [Protocol.CITY_WATER] = "LWT_CmdCityWater",
    [Protocol.SWITCH_VALVE] = "LWT_CmdSwitchValve",
    [Protocol.SET_TIMER] = "LWT_CmdSetTimer",
    [Protocol.SHOW_NETWORK] = "LWT_CmdShowNetwork",
    [Protocol.REMOVE_ALL] = "LWT_CmdRemoveAll",
}

local MODDATA_KEY = "LiveWater"

local function log(message)
    print(message)
end

-- Stateless game adapters, needed before OnInitGlobalModData (Live Wire registration).
-- Barrels a pump may stand against (ADR-011 D01): the same rule as the fittings' containers.
local BARRELS = { registry = LiveWater.Containers, listed = GameSettings.listedContainers }
local world = GameWorld.new(LiveWater.Parts, LiveWater.Sources, BARRELS)
local power = Power.new({ catalog = LiveWater.Parts, world = world })

local function randomShare()
    return ZombRandFloat(0, 1)
end

local function gameHours()
    return getGameTime():getWorldAgeHours()
end

-- A part that pressurizes (a pump) is in the network of `part`.
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
    local removal
    local topology = Topology.new({ registry = registry, network = network, catalog = catalog,
        events = LiveWater.Events, sprites = sprites, sites = world, edges = world, log = log,
        closed = function() return removal ~= nil and removal:started() end })
    local sounds = GameSounds.new()
    local publisher = Publisher.new({ catalog = catalog, sprites = sprites, mirror = world, sounds = sounds,
        visuals = GameVisuals.new() })
    local plumbing = GamePlumbing.new()
    local relays = Relays.new({ store = store, plumbing = plumbing, world = world,
        setting = GameSettings.scale, catalog = catalog, registry = registry, log = log })
    local outlets = Outlets.new(catalog)
    outlets:register("houseInlet", relays)
    local farming = GameFarming.new()
    outlets:register("sprinkler", Plants.new({ farming = farming, area = SprayArea.reach(catalog, GameSettings.scale) }))
    outlets:register("drip", Plants.new({ farming = farming,
        area = DripArea.reach(catalog, network, GameSettings.scale) }))
    local listed = BARRELS.listed
    local fittings = Fittings.new({ catalog = catalog, registry = registry, world = world,
        containers = GameContainers.new({ registry = LiveWater.Containers, listed = listed }),
        shapes = LiveWater.Containers, listed = listed, publisher = publisher })
    outlets:register("barrelFill", fittings)
    -- the consumers of other mods (LiveWater.API.registerOutlet, ADR-012 D04)
    local adopted = outlets:adopt(LiveWater.OutletTypes)
    if adopted > 0 then log("LiveWater: " .. adopted .. " outlet type(s) of other mods") end
    local function pumped(part) return hasPump(network, catalog, part) end
    local diagnostics = Diagnostics.new({ relays = relays, pumped = pumped })
    local washerFix = WasherFix.new({ relays = relays, plumbing = plumbing, multiplayer = isServer,
        enabled = function() return GameSettings.scale("WasherFix") ~= false end })
    removal = Removal.new({ store = store, registry = registry, topology = topology, world = world, log = log })
    local commands = Commands.new({ topology = topology, catalog = catalog, world = world,
        players = players, publisher = publisher, scale = GameSettings.scale,
        plumbing = plumbing, events = LiveWater.Events, replies = replies, removal = removal, relays = relays })
    for name, file in pairs(COMMANDS) do
        commands:register(name, require("LiveWater/Commands/" .. file))
    end
    -- walls and fences built without an event (ADR-002 D05): judged again at each clock step
    local edgeWatch = { tick = function() topology:refreshCuts(function(x, y, z) return world:isLoaded(x, y, z) end) end }
    local server = {
        world = world,
        registry = registry, network = network, topology = topology, commands = commands,
        publisher = publisher, power = power, outlets = outlets, relays = relays,
        fittings = fittings, valveSounds = ValveSounds.new(sounds),
        placement = Placement.new(topology, catalog, log, world, notifier(players)),
        clock = Clock.new({ network = network, flow = Flow.new(catalog), catalog = catalog,
            events = LiveWater.Events, power = power, publisher = publisher, scale = GameSettings.scale,
            random = randomShare, hours = gameHours, sources = LiveWater.Sources, chores = { removal, relays, diagnostics, washerFix, fittings, edgeWatch },
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
    if world:isEdgeObject(obj) then server.placement:edgeChanged(x, y, z) end
    if WaterObjects.changesSources(obj) then server.relays:touched(x, y, z) end
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
    if world:isEdgeObject(obj) then
        world:without(obj, function() server.placement:edgeChanged(x, y, z) end)
    end
    if WaterObjects.changesSources(obj) then server.relays:touched(x, y, z) end
end

-- Width of a chunk in squares (IsoChunk, Java 42.22).
local CHUNK_SQUARES = 8

local function onLoadChunk(chunk)
    local server = LiveWater.Server
    local sq = server and chunk and chunk:getGridSquare(0, 0, 0)
    if not sq then return end
    local x, y = sq:getX(), sq:getY()
    server.relays:chunkLoaded(x, y, CHUNK_SQUARES)
    server.fittings:chunkLoaded(x, y, CHUNK_SQUARES)
    server.publisher:chunkLoaded(x, y, CHUNK_SQUARES)
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
end

local function onWaterDelivered(part, litres, quality)
    local server = LiveWater.Server
    if server then server.outlets:deliver(part, litres, quality) end
end

local function onWaterDrawn(part, litres)
    local server = LiveWater.Server
    if server then server.fittings:drawn(part, litres) end
end

local function onNetworkChanged(id)
    local server = LiveWater.Server
    if server then server.clock:settle(id) end
end

-- A player opened or closed a valve: heard once (ADR-008 D10); the water follows at once and a house
-- kept from it loses its relays' water (ADR-010 D02-D04).
local function onValveChanged(part, open)
    local server = LiveWater.Server
    if not server then return end
    server.valveSounds:changed(part, open)
    local cut = server.clock:switched(part, open)
    for i = 1, #cut do server.outlets:cut(cut[i]) end
end

-- A generator started or stopped, or the public grid went off (ADR-008 D11).
local function onElectricityChanged()
    local server = LiveWater.Server
    if server then server.clock:powerChanged() end
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
LiveWater.Events.on("networkChanged", onNetworkChanged)
LiveWater.Events.on("valveChanged", onValveChanged)
Events.OnElectricityChanged.Add(onElectricityChanged)
Events.OnObjectAdded.Add(onObjectAdded)
Events.OnObjectAboutToBeRemoved.Add(onObjectAboutToBeRemoved)
Events.LoadChunk.Add(onLoadChunk)
Events.OnClientCommand.Add(onClientCommand)
Events.EveryTenMinutes.Add(onTenMinutes)

return LiveWater
