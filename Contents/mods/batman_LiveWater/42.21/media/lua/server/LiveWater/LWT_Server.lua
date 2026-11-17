if isClient() then return end
-- LiveWater: composition root on the authority (solo game or server). Builds the services with
-- their game adapters at OnInitGlobalModData (the global ModData is reloaded just before it:
-- never keep a table of an earlier game) and wires the game events, each once:
--   OnObjectAdded / OnObjectAboutToBeRemoved  -> LWT_Placement
--   OnClientCommand (module LiveWater)        -> LWT_Commands
--   EveryTenMinutes                           -> LWT_Clock (the only clock, ADR-001 D09)
--   OnInitWorld                               -> LWT_Power:register (Live Wire consumers, D20)
--   LiveWater.Events partAdded / partRemoved  -> LWT_Publisher (sprite by state, mirrored state)
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
local Power = require "LiveWater/LWT_Power"
local Publisher = require "LiveWater/LWT_Publisher"

-- Command name -> handler file under LiveWater/Commands.
local COMMANDS = {
    [Protocol.LAY] = "LWT_CmdLay",
    [Protocol.DISMANTLE] = "LWT_CmdDismantle",
    [Protocol.FIT_FILTER] = "LWT_CmdFitFilter",
    [Protocol.REMOVE_FILTER] = "LWT_CmdRemoveFilter",
}

local MODDATA_KEY = "LiveWater"

local function log(message)
    print(message)
end

-- Stateless game adapters, needed before OnInitGlobalModData (Live Wire registration).
local world = GameWorld.new(LiveWater.Parts, LiveWater.Sources)
local power = Power.new({ catalog = LiveWater.Parts, world = world })

local function build()
    local catalog = LiveWater.Parts
    local registry = Registry.new(ModData.getOrCreate(MODDATA_KEY), catalog)
    local network = Network.new(catalog)
    local sprites = Sprites.new(network, catalog, world)
    local topology = Topology.new({ registry = registry, network = network, catalog = catalog,
        events = LiveWater.Events, sprites = sprites, sites = world, log = log })
    local publisher = Publisher.new({ catalog = catalog, sprites = sprites, mirror = world })
    local commands = Commands.new({ topology = topology, catalog = catalog, world = world,
        players = GamePlayers.new(), publisher = publisher, scale = GameSettings.scale })
    for name, file in pairs(COMMANDS) do
        commands:register(name, require("LiveWater/Commands/" .. file))
    end
    local server = {
        registry = registry, network = network, topology = topology, commands = commands,
        publisher = publisher, power = power,
        placement = Placement.new(topology, catalog, log, world),
        clock = Clock.new({ network = network, flow = Flow.new(catalog), catalog = catalog, world = world,
            events = LiveWater.Events, power = power, publisher = publisher, scale = GameSettings.scale }),
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
    if name then server.placement:added(name, x, y, z) end
end

local function onObjectAboutToBeRemoved(obj)
    local server = LiveWater.Server
    if not server then return end
    local name, x, y, z = whereIs(obj)
    if name then server.placement:removed(name, x, y, z) end
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
    if server then server.publisher:forget(entry) end
end

local function onTenMinutes()
    local server = LiveWater.Server
    if server then server.clock:tick() end
end

Events.OnInitWorld.Add(onInitWorld)
Events.OnInitGlobalModData.Add(onInit)
LiveWater.Events.on("partAdded", onPartAdded)
LiveWater.Events.on("partRemoved", onPartRemoved)
Events.OnObjectAdded.Add(onObjectAdded)
Events.OnObjectAboutToBeRemoved.Add(onObjectAboutToBeRemoved)
Events.OnClientCommand.Add(onClientCommand)
Events.EveryTenMinutes.Add(onTenMinutes)

return LiveWater
