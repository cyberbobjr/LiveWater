"""Offline static checks of the LiveWater mod (no game needed).

Run: python -B tools/check_mod.py
Checks:
  1. every .lua file is ASCII and compiles as Lua 5.1 (Kahlua is close to 5.1);
  2. every file loads in game order (shared, client, server; lower-case path) in a
     permissive stub environment, require resolving this mod's own modules once;
  3. every file in lua/server starts with the isClient() guard;
  4. no subscription to a per-frame event (ADR-001 D08), except Events.OnTick in the one client
     file of the animated sprinkler jet (ADR-001 D08a, PER_FRAME_ALLOWED);
  5. translations: EN and FR have the same files and keys, every other language
     uses EN keys only, and every getText key used in Lua exists in EN.
Passing these checks proves nothing about in-game behaviour.
"""
import glob
import json
import os
import re
import sys

from lupa import lua51

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
LUA = os.path.join(MEDIA, "lua")
SIDES = ("shared", "client", "server")
PER_FRAME = ("OnTick", "OnTickEvenPaused", "OnPlayerUpdate", "OnRenderTick", "OnPostRender",
             "OnPreUIDraw", "OnPostUIDraw", "OnFETick", "OnRenderUpdate")
# ADR-001 D08a: the only per-frame subscription allowed, Events.OnTick in the client module of the
# animated sprinkler jet (subscribed only while a sprinkler sprays nearby). Nowhere else.
PER_FRAME_ALLOWED = {"client/LiveWater/LWT_SprinklerJet.lua": {"OnTick"}}
FAILS = []


def fail(msg):
    FAILS.append(msg)
    print("FAIL:", msg)


def side_files(side):
    files = glob.glob(os.path.join(LUA, side, "**", "*.lua"), recursive=True)
    files = [p for p in files if os.sep + "Translate" + os.sep not in p]
    return sorted(files, key=lambda p: os.path.relpath(p, os.path.join(LUA, side)).lower())


def rel(path):
    return os.path.relpath(path, LUA).replace(os.sep, "/")


STUBS = r"""
local Stub = {}
local mt = {}
mt.__index = function() return Stub end
mt.__call = function() return Stub end
setmetatable(Stub, mt)
Events = setmetatable({}, { __index = function(t, k)
    local e = { Add = function() end, Remove = function() end }
    rawset(t, k, e)
    return e
end })
function isClient() return false end
function isServer() return false end
setmetatable(_G, { __index = function() return Stub end })
LWT_SOURCES, LWT_LOADED = {}, {}
function require(path)
    if string.sub(path, -4) == ".lua" then path = string.sub(path, 1, -5) end
    if LWT_LOADED[path] ~= nil then return LWT_LOADED[path] end
    local src = LWT_SOURCES[path]
    if src == nil then return nil end
    local value = assert(loadstring(src, path))()
    if value == nil then value = true end
    LWT_LOADED[path] = value
    return value
end
function LWT_RUN(path, src)
    if LWT_LOADED[path] ~= nil then return end
    local value = assert(loadstring(src, path))()
    if value == nil then value = true end
    LWT_LOADED[path] = value
end
"""


def check_lua():
    files = [p for side in SIDES for p in side_files(side)]
    sources = {}
    for p in files:
        data = open(p, "rb").read()
        try:
            text = data.decode("ascii")
        except UnicodeDecodeError:
            fail("%s: non-ASCII byte (Kahlua)" % rel(p))
            continue
        sources[p] = text
        lua = lua51.LuaRuntime()
        ok, err = lua.execute("return function(s, n) local f, e = loadstring(s, n) return f ~= nil, e end")(text, rel(p))
        if not ok:
            fail("%s: %s" % (rel(p), err))
        if os.sep + "server" + os.sep in p and not re.match(r"\s*if\s+isClient\(\)\s+then\s+return", text):
            fail("%s: server file without the isClient() guard on its first line" % rel(p))
        for ev in PER_FRAME:
            if ev in PER_FRAME_ALLOWED.get(rel(p), ()):
                continue
            if re.search(r"Events\.%s\b" % ev, text):
                fail("%s: per-frame event %s (D08)" % (rel(p), ev))
    lua = lua51.LuaRuntime()
    lua.execute(STUBS)
    by_path = {}
    for side in SIDES:
        for p in side_files(side):
            key = os.path.splitext(os.path.relpath(p, os.path.join(LUA, side)))[0].replace(os.sep, "/")
            by_path[p] = key
            lua.globals().LWT_SOURCES[key] = sources.get(p, "")
    for p in files:
        if p not in sources:
            continue
        try:
            lua.globals().LWT_RUN(by_path[p], sources[p])
        except Exception as e:  # lupa.LuaError
            fail("%s: load error: %s" % (rel(p), e))
    return files, sources


def check_translations(sources):
    tr = os.path.join(LUA, "shared", "Translate")
    if not os.path.isdir(tr):
        return
    langs = {d: {} for d in os.listdir(tr) if os.path.isdir(os.path.join(tr, d))}
    for lang in langs:
        for p in glob.glob(os.path.join(tr, lang, "*.json")):
            try:
                langs[lang][os.path.basename(p)] = json.load(open(p, encoding="utf-8"))
            except ValueError as e:
                fail("%s: invalid JSON: %s" % (rel(p), e))
    en, fr = langs.get("EN", {}), langs.get("FR", {})
    if set(en) != set(fr):
        fail("Translate: EN and FR files differ: %s" % sorted(set(en) ^ set(fr)))
    en_keys = {k for d in en.values() for k in d}
    fr_keys = {k for d in fr.values() for k in d}
    for k in sorted(en_keys ^ fr_keys):
        fail("Translate: key %s missing in %s" % (k, "FR" if k in en_keys else "EN"))
    for lang, files in langs.items():
        for k in sorted({k for d in files.values() for k in d} - en_keys):
            fail("Translate/%s: key %s unknown in EN" % (lang, k))
    for p, text in sources.items():
        for k in re.findall(r'getText\(\s*"([^"]+)"', text):
            if k not in en_keys:
                fail("%s: getText key %s missing in EN" % (rel(p), k))


def main():
    if not os.path.isdir(LUA):
        fail("missing %s" % LUA)
    files, sources = check_lua()
    check_translations(sources)
    if FAILS:
        print("FAILED: %d problem(s)" % len(FAILS))
        return 1
    print("OK: %d Lua file(s) checked" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
