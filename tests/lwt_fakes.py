"""Lua test doubles of the E07 game ports (world squares and objects, players) and a builder of the
server services around them. They stand for LWT_GameWorld and LWT_GamePlayers, which call the game.

Test part types:
  Test:Pipe   16 sprites t_pipe_0..15, conduit, layable with Test.Section (tool tag base:pipewrench)
  Test:Pump   one sprite t_pump, intake + pump (ports given by PUMP_PORTS, default 4)
  Test:Spr    one sprite t_spr, sprinkler outlet
"""

PARTS = r"""
local pipe = {}
for m = 0, 15 do pipe[m] = "t_pipe_" .. m end
LiveWater.API.registerPart("Test:Pipe", { sprites = pipe,
    capabilities = { conduit = true, layable = { item = "Test.Section" } } })
LiveWater.API.registerPart("Test:Pump", { sprites = { [0] = "t_pump" },
    capabilities = { intake = true, pump = { ports = PUMP_PORTS or 4 } } })
LiveWater.API.registerPart("Test:Spr", { sprites = { [0] = "t_spr" },
    capabilities = { outlet = { type = "sprinkler" } } })
"""

FAKES = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end

FakeWorld = {}
FakeWorld.__index = FakeWorld
function FakeWorld.new(catalog)
    return setmetatable({ catalog = catalog, unloaded = {}, blocked = {}, objects = {}, sets = 0 }, FakeWorld)
end
function FakeWorld:list(x, y, z)
    local l = self.objects[k(x, y, z)]
    if not l then l = {} self.objects[k(x, y, z)] = l end
    return l
end
function FakeWorld:isLoaded(x, y, z) return not self.unloaded[k(x, y, z)] end
function FakeWorld:isFree(x, y, z) return not self.blocked[k(x, y, z)] end
function FakeWorld:spriteOf(x, y, z, typeId)
    if self.unloaded[k(x, y, z)] then return nil end
    for _, s in ipairs(self:list(x, y, z)) do
        if self.catalog:typeOfSprite(s) == typeId then return s end
    end
    return nil
end
function FakeWorld:setSprite(x, y, z, typeId, name)
    local l = self:list(x, y, z)
    for i, s in ipairs(l) do
        if self.catalog:typeOfSprite(s) == typeId then l[i] = name self.sets = self.sets + 1 return true end
    end
    return false
end
function FakeWorld:createPart(x, y, z, name) table.insert(self:list(x, y, z), name) return true end
function FakeWorld:removePart(x, y, z, typeId)
    local l = self:list(x, y, z)
    for i, s in ipairs(l) do
        if self.catalog:typeOfSprite(s) == typeId then table.remove(l, i) return true end
    end
    return false
end
function FakeWorld:sprite(x, y, z) return self:list(x, y, z)[1] end

FakePlayers = {}
FakePlayers.__index = FakePlayers
function FakePlayers.new() return setmetatable({}, FakePlayers) end
function FakePlayers:position(p) return p.x, p.y, p.z end
function FakePlayers:has(p, fullType) return (p.items[fullType] or 0) > 0 end
function FakePlayers:take(p, fullType)
    if (p.items[fullType] or 0) <= 0 then return false end
    p.items[fullType] = p.items[fullType] - 1
    return true
end
function FakePlayers:give(p, fullType) p.items[fullType] = (p.items[fullType] or 0) + 1 return true end
function FakePlayers:hasTool(p, tag) return p.tools[tag] == true end
function FakePlayers:tell(p, key) table.insert(p.told, key) end

function newPlayer(x, y, z, items, tools)
    return { x = x, y = y, z = z or 0, items = items or {}, tools = tools or {}, told = {} }
end

EMITTED = {}
for _, name in ipairs({ "partAdded", "partRemoved", "networkChanged", "waterDelivered", "valveChanged" }) do
    LiveWater.Events.on(name, function(...) table.insert(EMITTED, { name, ... }) end)
end
function emitted(name)
    local out = {}
    for _, e in ipairs(EMITTED) do if e[1] == name then table.insert(out, e) end end
    return out
end

LOGS = {}
function newServices(store)
    STORE = store or {}
    WORLD = FakeWorld.new(LiveWater.Parts)
    PLAYERS = FakePlayers.new()
    REG = require("LiveWater/LWT_Registry").new(STORE, LiveWater.Parts)
    NET = require("LiveWater/LWT_Network").new(LiveWater.Parts)
    SPRITES = require("LiveWater/LWT_Sprites").new(NET, LiveWater.Parts, WORLD)
    TOPO = require("LiveWater/LWT_Topology").new({ registry = REG, network = NET, catalog = LiveWater.Parts,
        events = LiveWater.Events, sprites = SPRITES, log = function(m) table.insert(LOGS, m) end })
end

-- A part placed as the game would: its object on the square, then the topology.
function place(t, x, y, sprite)
    WORLD:createPart(x, y, 0, sprite or LiveWater.Parts:sprite(t, 0))
    return TOPO:add(t, x, y, 0)
end
"""


def services(lua_new, *extra_files, pump_ports=None):
    files = ("shared/LiveWater/LWT_API.lua",) + extra_files
    lua = lua_new(*files)
    if pump_ports is not None:
        lua.execute("PUMP_PORTS = %d" % pump_ports)
    lua.execute(PARTS)
    lua.execute(FAKES)
    lua.execute("newServices()")
    return lua
