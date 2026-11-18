"""Offline test bench of LiveWater: embedded Lua 5.1 (pip install lupa).

new_lua(*files) builds a fresh runtime with a minimal game stub and runs the given
mod files (paths under media/lua, e.g. "shared/LiveWater/LWT_API.lua") in order.
require() resolves this mod's own modules from shared, client and server, runs
each once and memoises its return value, as the game's LuaManager does.
Tests prove the Lua logic only, never the engine.
Run: python -B -m unittest discover -s tests
"""
import os

from lupa import lua51

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media", "lua")

PRELUDE = r"""
Events = setmetatable({}, { __index = function(t, k)
    local e = { handlers = {} }
    function e.Add(fn) table.insert(e.handlers, fn) end
    function e.Remove(fn)
        for i = #e.handlers, 1, -1 do if e.handlers[i] == fn then table.remove(e.handlers, i) end end
    end
    rawset(t, k, e)
    return e
end })
function fire(name, ...)
    for _, fn in ipairs(Events[name].handlers) do fn(...) end
end
function isClient() return false end
function isServer() return false end
LWT_LOADED = {}
-- Timed actions of the client menus: queued actions run at once (walk and duration not simulated).
ISBaseTimedAction = { Type = "ISBaseTimedAction" }
ISBaseTimedAction.__index = ISBaseTimedAction
function ISBaseTimedAction:derive(name)
    local o = setmetatable({}, self)
    self.__index = self
    o.Type = name
    return o
end
function ISBaseTimedAction.new(self, character)
    local o = setmetatable({}, self)
    self.__index = self
    o.character = character
    return o
end
function ISBaseTimedAction:perform() end
function ISBaseTimedAction:setActionAnim() end
QUEUED, WALKED = {}, {}
ISTimedActionQueue = { add = function(action) table.insert(QUEUED, action) action:perform() return action end }
luautils = { walkAdj = function(player, sq) table.insert(WALKED, sq) return true end }
function require(path)
    if string.sub(path, -4) == ".lua" then path = string.sub(path, 1, -5) end
    if LWT_LOADED[path] ~= nil then return LWT_LOADED[path] end
    local src = LWT_FIND(path)
    if src == nil then return nil end
    local value = assert(loadstring(src, path))()
    if value == nil then value = true end
    LWT_LOADED[path] = value
    return value
end
"""


def read(rel):
    with open(os.path.join(LUA, rel), encoding="ascii") as f:
        return f.read()


def find(path):
    for side in ("shared", "client", "server"):
        p = os.path.join(LUA, side, path + ".lua")
        if os.path.isfile(p):
            with open(p, encoding="ascii") as f:
                return f.read()
    return None


def new_lua(*files):
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.globals().LWT_FIND = find
    lua.execute(PRELUDE)
    for rel in files:
        side, key = rel.split("/", 1)
        key = os.path.splitext(key)[0]
        if lua.eval("LWT_LOADED[%r]" % key) is None:
            fn = lua.execute("return function(src, name) return assert(loadstring(src, name)) end")(read(rel), rel)
            value = fn()
            lua.globals().LWT_LOADED[key] = True if value is None else value
    return lua
