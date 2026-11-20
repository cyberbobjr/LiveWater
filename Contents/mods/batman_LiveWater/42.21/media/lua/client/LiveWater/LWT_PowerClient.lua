-- LiveWater: Live Wire consumers on a multiplayer client (ADR-017 D03). Live Wire's client menus
-- (Connect to an inverter, Connections window, displayName) find a consumer by its sprite in the
-- client's own registry, so a client registers the same part types as the authority
-- (LWT_LiveWireConsumers: sprites, category, circuit, link), without any server state: no draw
-- (powerConsumption 0, the authority bills), no display (Live Wire then names the part by its tile),
-- no summary. A single player game has one Lua state: LWT_Power registers there, not this file.
-- Moment: OnInitWorld, after every mod's Lua is loaded and before Live Wire seals its registrations
-- at OnInitGlobalModData, on a client as on the authority. Both events are fired by
-- IsoWorld.init() (Java 42.22, zombie/iso/IsoWorld.java): OnInitWorld at line 1811, then
-- GlobalModData.instance.init() at line 1921, which fires OnInitGlobalModData
-- (zombie/world/moddata/GlobalModData.java line 55); no GameClient.client branch skips either
-- (the early returns in between only abort a failed connection).

require "LiveWater/LWT_API"
local Consumers = require "LiveWater/LWT_LiveWireConsumers"

local function noDraw()
    return 0
end

local function complete(_, def)
    def.powerConsumption = noDraw
end

local function onInitWorld()
    local count = Consumers.register(LiveWire and LiveWire.API, LiveWater.Parts, complete)
    if count > 0 then print("LiveWater: " .. count .. " part type(s) registered as Live Wire consumers (client)") end
end

if isClient() then Events.OnInitWorld.Add(onInitWorld) end
