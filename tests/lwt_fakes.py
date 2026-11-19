"""Lua test doubles of the E07 game ports (world squares and objects, players) and a builder of the
server services around them. They stand for LWT_GameWorld and LWT_GamePlayers, which call the game.

Test part types:
  Test:Pipe   16 sprites t_pipe_0..15, conduit; sleeves t_pipe_<mask>_x<edges> for masks with N (edges 1), W (8),
              both (9), except mask 5 (N + S) which has none
  Test:Pump   one sprite t_pump, intake + pump (ports given by PUMP_PORTS, default 4)
  Test:Spr    one sprite t_spr, sprinkler outlet
"""

PARTS = r"""
local pipe = {}
for m = 0, 15 do pipe[m] = "t_pipe_" .. m end
local crossings = {}
for m = 0, 15 do
    if m ~= 5 then
        local c = {}
        if m % 2 == 1 then c[1] = "t_pipe_" .. m .. "_x1" end
        if m >= 8 then c[8] = "t_pipe_" .. m .. "_x8" end
        if m % 2 == 1 and m >= 8 then c[9] = "t_pipe_" .. m .. "_x9" end
        if next(c) then crossings[m] = c end
    end
end
LiveWater.API.registerPart("Test:Pipe", { sprites = pipe, crossings = crossings,
    capabilities = { conduit = true } })
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
    return setmetatable({ catalog = catalog, unloaded = {}, objects = {}, sets = 0, dry = {}, near = {},
        unpowered = {}, generators = {}, gridOff = false, states = {}, writes = 0, things = {}, edges = {} }, FakeWorld)
end
-- Edges port (ADR-002 D04): kind of the N (north = true) or W edge of a square, "wall", "fence" or nil.
function FakeWorld:setEdge(x, y, z, north, kind) self.edges[k(x, y, z) .. (north and "N" or "W")] = kind end
function FakeWorld:edge(x, y, z, north) return self.edges[k(x, y, z) .. (north and "N" or "W")] end
-- Neighbourhood probe of a square: natural water everywhere unless dry[key]; near[key] = set of sprites around.
function FakeWorld:site(x, y, z)
    local world, key = self, k(x, y, z)
    local probe = {
        hasFlag = function(_, name) return name == "water" and not world.dry[key] end,
        hasSprite = function(_, name) return (world.near[key] or {})[name] == true end,
    }
    function probe:source() return LiveWater.Sources:find(self) end
    return probe
end
-- Current of a loaded square: a generator in range (generators[key]) and the public grid there (unless
-- unpowered[key] or the grid is off everywhere, gridOff); nil when not loaded.
function FakeWorld:powerAt(x, y, z)
    local key = k(x, y, z)
    if self.unloaded[key] then return nil end
    return self.generators[key] == true, not self.unpowered[key] and not self.gridOff
end
function FakeWorld:gridRuns() return not self.gridOff end
function FakeWorld:hasPower(x, y, z)
    local key = k(x, y, z)
    return self.generators[key] == true or (not self.unpowered[key] and not self.gridOff)
end
-- Stand-in of the game object of a part (one per square and type), with the mirrored state.
function FakeWorld:object(x, y, z, typeId)
    local key = k(x, y, z) .. "," .. typeId
    local obj = self.things[key]
    if not obj then
        obj = { x = x, y = y, z = z, typeId = typeId }
        self.things[key] = obj
    end
    return obj
end
local function copy(v)
    if type(v) ~= "table" then return v end
    local out = {}
    for a, b in pairs(v) do out[a] = copy(b) end
    return out
end
function FakeWorld:writeState(x, y, z, typeId, state)
    self.states[k(x, y, z)] = copy(state)
    self.writes = self.writes + 1
    return true
end
function FakeWorld:stateOf(x, y, z, typeId)
    local s = self.states[k(x, y, z)]
    if s and s.type == typeId then return s end
    return nil
end
-- What LWT_Mirror.read gives for a stand-in object.
function FakeWorld:stateOfObject(obj) return self:stateOf(obj.x, obj.y, obj.z, obj.typeId) end
function FakeWorld:list(x, y, z)
    local l = self.objects[k(x, y, z)]
    if not l then l = {} self.objects[k(x, y, z)] = l end
    return l
end
function FakeWorld:isLoaded(x, y, z) return not self.unloaded[k(x, y, z)] end
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
function FakePlayers:count(p, fullType) return p.items[fullType] or 0 end
-- take answers the share of the item left (its condition), p.fractions[fullType] or 1.
function FakePlayers:take(p, fullType)
    if (p.items[fullType] or 0) <= 0 then return false end
    p.items[fullType] = p.items[fullType] - 1
    return true, (p.fractions or {})[fullType] or 1
end
function FakePlayers:give(p, fullType, fraction)
    p.items[fullType] = (p.items[fullType] or 0) + 1
    table.insert(p.given, { type = fullType, fraction = fraction })
    return true
end
function FakePlayers:hasTool(p, tag) return p.tools[tag] == true end
function FakePlayers:tell(p, key) table.insert(p.told, key) end

function newPlayer(x, y, z, items, tools)
    return { x = x, y = y, z = z or 0, items = items or {}, tools = tools or {}, told = {}, given = {} }
end

EMITTED = {}
for _, name in ipairs(require("LiveWater/LWT_Events").NAMES) do
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
        events = LiveWater.Events, sprites = SPRITES, sites = WORLD, edges = WORLD, log = function(m) table.insert(LOGS, m) end })
end

-- A part placed as the game would: its object on the square, then the topology.
function place(t, x, y, sprite)
    WORLD:createPart(x, y, 0, sprite or LiveWater.Parts:sprite(t, 0))
    return TOPO:add(t, x, y, 0, nil, LiveWater.Parts:facingOf(sprite or ""))
end
"""


# Containers port of the barrel fittings (LWT_GameContainers): CONT["x,y"] = { amount, capacity, fluid, sprite }.
CONTAINERS = r"""
CONT = {}
CONTAINERS = {}
function CONTAINERS:at(x, y, z)
    local c = CONT[x .. "," .. y]
    if not c then return nil end
    return { fluid = c.amount > 0 and c.fluid or nil, amount = c.amount, free = c.capacity - c.amount, sprite = c.sprite }
end
function CONTAINERS:add(x, y, z, litres, quality)
    local c = CONT[x .. "," .. y]
    c.amount = c.amount + litres
    c.fluid = quality
    return litres
end
function CONTAINERS:take(x, y, z, litres)
    local c = CONT[x .. "," .. y]
    c.amount = c.amount - litres
    return litres
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
