--[[
Hooks of the generic launcher pzdev (PZDevKit) for LiveWater: nominal end-to-end path (E22). Configuration:
LiveWater/autotest.json. Loaded by batman_PZDevKit with loadstring (global environment, the mod already
loaded). ASCII only (Kahlua lexer). Every change happens in the COPIED save of pzdev.

Solo (client hooks: authority and client in one process):
  1. the player is made untouchable (god mode, invisible); zombies are cleared at every poll;
  2. a layout is searched around candidate places (params `centers`, "x,y;x,y"): a free square next to natural
     water (pond pump), a free outdoor square against a map building holding a water fixture (house inlet), a
     chain of free squares between them (pipes, breadth-first search), a free square beside one pipe (manual
     sprinkler), a square within its radius (crop), a later chain square between two pipes (inline valve), a
     square near the pump (generator);
  3. fixtures (named as such in the report): a vanilla generator (IsoGenerator, fuelled, connected, on), a
     carrot crop through the vanilla farming system (SFarmingSystem:plow then SPlantGlobalObject:seed, water
     level set to 0), the fixture plumbed as ISPlumbItem:complete does;
  4. the pump, the inlet, the sprinkler and the valve are set down through the real moveable placement
     (ISMoveableSpriteProps:placeMoveable, what ISMoveablesAction:complete calls), with the moveable items;
  5. pipes, filter and valve go through the real client commands (sendClientCommand, module LiveWater: lay,
     switchValve, fitFilter), queued in solo and handled by the authority's dispatcher;
  6. time runs in fast forward and the real EveryTenMinutes steps are counted (no direct clock call).
Checks: network built (one network), pipe sprites by side mask, pump powered and running, sprinkler served
and the plant's water level up, house inlet refused without filter (state unfiltered, amber sprite, relays
empty), then with the filter served (green sprite, relay filled, the fixture gives clean water), the
inline valve closed stops the house downstream while the sprinkler upstream still waters (relays emptied and
crop dried first: fixture), the sprinkler valve closed stops the branch (state closed, plant level unchanged),
no Lua error. A phase is judged on every ten-minute step it ran (the pump stops when no outlet needs water).
Parameters (ctx.params, text): centers, radius (scan radius, default 40), stepSec (deadline of one ten-minute
step, default 90).
]]

local H = { client = {}, server = {} }

local MODULE = "LiveWater"
local SHEET = "batman_livewater_01_"
local PIPE = "LiveWater:PipeGalvanized"
local PUMP_SPRITE, INLET_SPRITE, SPRINKLER_SPRITE = SHEET .. "24", SHEET .. "40", SHEET .. "48"
local VALVE_SPRITE, VALVE = SHEET .. "16", "LiveWater:Valve"
local METER_SPRITE, FITTING_SPRITE = SHEET .. "20", SHEET .. "64"
local SIDES = { { 0, -1, 1 }, { 1, 0, 2 }, { 0, 1, 4 }, { -1, 0, 8 } }

-- ------------------------------------------------------------------ report

local R = { lines = {}, ok = true, steps = {}, index = 0 }

local function rec(ok, name, detail)
    if not ok then R.ok = false end
    R.lines[#R.lines + 1] = (ok and "PASS " or "FAIL ") .. name .. (detail ~= nil and (" - " .. tostring(detail)) or "")
end

local function info(text)
    R.lines[#R.lines + 1] = "INFO " .. tostring(text)
    print("LWT-TEST " .. tostring(text))
end

local function nowMs()
    return getTimestampMs()
end

local function addStep(name, fn, limitSec)
    R.steps[#R.steps + 1] = { name = name, fn = fn, limitMs = (limitSec or 10) * 1000 }
end

local function runSteps()
    while true do
        local step = R.steps[R.index + 1]
        if not step then return true end
        if not step.started then step.started = nowMs() end
        local ok, res = pcall(step.fn)
        if not ok then
            rec(false, step.name, "error: " .. tostring(res))
            R.index = #R.steps
            return true
        elseif res == true then
            R.index = R.index + 1
        elseif res == "abort" then
            R.index = #R.steps
            return true
        elseif nowMs() - step.started > step.limitMs then
            rec(false, step.name, "timeout after " .. tostring(math.floor(step.limitMs / 1000)) .. " s")
            R.index = #R.steps
            return true
        else
            return false
        end
    end
end

local function summary()
    local pass, total = 0, 0
    for i = 1, #R.lines do
        local head = R.lines[i]:sub(1, 4)
        if head == "PASS" then pass = pass + 1 end
        if head == "PASS" or head == "FAIL" then total = total + 1 end
    end
    return { ok = R.ok and total > 0, summary = tostring(pass) .. "/" .. tostring(total) .. " PASS", lines = R.lines }
end

-- ------------------------------------------------------------------ world helpers

local function sq(x, y, z)
    return getCell():getGridSquare(x, y, z or 0)
end

local function key(x, y)
    return x .. "," .. y
end

local function near(p, q, d)
    return math.abs(p.x - q.x) <= d and math.abs(p.y - q.y) <= d
end

local function clearZombies()
    local list = getCell():getZombieList()
    for i = list:size() - 1, 0, -1 do
        local z = list:get(i)
        z:removeFromWorld()
        z:removeFromSquare()
    end
end

local function hasWater(s)
    return s ~= nil and s:has(IsoFlagType.water)
end

-- Free for a part (the rule of LWT_GameWorld:isFree), outdoors, nothing else standing there. `wallOk`: a wall
-- on the square's own edge is allowed (a house's south or east wall belongs to the outside square along it).
local function free(s, wallOk)
    if not s or not s:getFloor() then return false end
    if s:has(IsoFlagType.water) or s:isSolid() or s:isSolidTrans() or s:HasTree() then return false end
    if not s:isOutside() or s:getBuilding() ~= nil then return false end
    local objects = s:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        local name = obj:getSpriteName() or ""
        local props = obj:getProperties()
        -- a plain wall only: no door, garage door or window in it
        local opening = instanceof(obj, "IsoDoor") or instanceof(obj, "IsoWindow") or instanceof(obj, "IsoWindowFrame")
            or (props ~= nil and (props:has(IsoFlagType.DoorWallN) or props:has(IsoFlagType.DoorWallW)
            or props:has(IsoFlagType.doorN) or props:has(IsoFlagType.doorW) or props:has(IsoFlagType.WindowN)
            or props:has(IsoFlagType.WindowW) or props:has(IsoFlagType.windowN) or props:has(IsoFlagType.windowW)))
            or string.find(string.lower(name), "garage", 1, true) ~= nil
        local wall = wallOk and not opening and props ~= nil and (props:has(IsoFlagType.WallN)
            or props:has(IsoFlagType.WallW) or props:has(IsoFlagType.WallNW))
        if obj ~= s:getFloor() and not wall and not (string.find(name, "^e_") or string.find(name, "^blends_")
            or string.find(name, "^vegetation_") or string.find(name, "^d_plants") or string.find(name, "^floors_")) then
            return false
        end
    end
    return true
end

local function nearWater(x, y)
    for dx = -1, 1 do
        for dy = -1, 1 do
            if (dx ~= 0 or dy ~= 0) and hasWater(sq(x + dx, y + dy)) then return true end
        end
    end
    return false
end

local function isFixture(obj)
    if instanceof(obj, "IsoWorldInventoryObject") then return false end
    local sprite = obj:getSprite()
    local props = sprite and sprite:getProperties()
    return props ~= nil and props:has(IsoFlagType.waterPiped)
end

local function mapBuilding(s)
    local b = s and s:getBuilding()
    local def = b and b:getDef()
    if def and not def:isUserDefined() then return def end
    return nil
end

local function fixtureOf(s)
    local objects = s:getObjects()
    for i = 0, objects:size() - 1 do
        if isFixture(objects:get(i)) then return objects:get(i) end
    end
    return nil
end

-- ------------------------------------------------------------------ layout search

-- Fixtures of map buildings within the scan: list of { x, y, def, obj }.
local function scanFixtures(cx, cy, r)
    local out = {}
    for x = cx - r, cx + r do
        for y = cy - r, cy + r do
            local s = sq(x, y, 0)
            local def = s and mapBuilding(s)
            if def then
                local obj = fixtureOf(s)
                if obj then out[#out + 1] = { x = x, y = y, def = def, obj = obj } end
            end
        end
    end
    return out
end

-- A free outdoor square orthogonally next to the building of `f`, within 15 squares of the fixture. `wallNorth`
-- (visual captures): only a square whose building is north or west of it, the inlet then hangs on a wall face
-- the camera sees (the camera always looks north-west): facing S (+0, backboard on its north edge) or E (+1).
-- `turn` is the facing offset of the inlet tile.
local function inletTargets(fixtures, cx, cy, r, wallNorth)
    local targets = {}
    for i = 1, #fixtures do
        local f = fixtures[i]
        for x = f.x - 15, f.x + 15 do
            for y = f.y - 15, f.y + 15 do
                local dx, dy = x - f.x, y - f.y
                if dx * dx + dy * dy <= 225 and math.abs(x - cx) <= r and math.abs(y - cy) <= r then
                    local s = sq(x, y, 0)
                    if free(s, wallNorth) and not nearWater(x, y) then
                        for j = 1, 4 do
                            local n = sq(x + SIDES[j][1], y + SIDES[j][2], 0)
                            local turn = (j == 1 and 0) or (j == 4 and 1) or nil
                            if n and mapBuilding(n) == f.def and not targets[key(x, y)]
                                and (not wallNorth or turn ~= nil) then
                                targets[key(x, y)] = { x = x, y = y, fixture = f, turn = turn or 0 }
                            end
                        end
                    end
                end
            end
        end
    end
    return targets
end

local function touchesAny(x, y, set, except)
    for j = 1, 4 do
        local k = key(x + SIDES[j][1], y + SIDES[j][2])
        if set[k] and k ~= except then return true end
    end
    return false
end

-- Breadth-first search from every pump square to the nearest inlet square through free squares. `withMeter`
-- (visual captures) also takes a straight pipe square, away from the valve, for a flow meter (L.meter), and
-- keeps only inlet squares with their house to the north (inletTargets, wallNorth).
local function findLayout(cx, cy, r, withMeter)
    local fixtures = scanFixtures(cx, cy, r)
    if #fixtures == 0 then return nil, "no fixture in map buildings" end
    -- a sink when there is one (the brief's plumbed sink), else any water fixture
    local sinks = {}
    for i = 1, #fixtures do
        if string.find(string.lower(tostring(fixtures[i].obj:getSpriteName())), "sink", 1, true) then
            sinks[#sinks + 1] = fixtures[i]
        end
    end
    if #sinks > 0 then fixtures = sinks end
    local targets = inletTargets(fixtures, cx, cy, r, withMeter)
    -- pump squares; `withMeter` (visual captures): water on one side only counts, the pump is turned so that
    -- its suction hose (south edge of the tile, facing S) dips into it, the line leaves on the opposite side
    -- (WATER_TURN: side index of SIDES -> facing offset of the pump tile; OUT: side the line leaves by)
    local WATER_TURN, OUT = { [3] = 0, [2] = 1, [1] = 2, [4] = 3 }, { [3] = 1, [2] = 4, [1] = 3, [4] = 2 }
    local queue, prev, head, starts = {}, {}, 1, {}
    for x = cx - r, cx + r do
        for y = cy - r, cy + r do
            if free(sq(x, y, 0)) and nearWater(x, y) then
                local side
                for j = 1, 4 do
                    if not side and hasWater(sq(x + SIDES[j][1], y + SIDES[j][2], 0)) then side = j end
                end
                if not withMeter or side then
                    queue[#queue + 1] = { x = x, y = y }
                    prev[key(x, y)] = "start"
                    starts[key(x, y)] = side and { turn = WATER_TURN[side], out = OUT[side] } or { turn = 0 }
                end
            end
        end
    end
    if #queue == 0 then return nil, "no free square next to water (fixtures " .. #fixtures .. ")" end
    local goal
    while head <= #queue do
        local n = queue[head]
        head = head + 1
        local t = targets[key(n.x, n.y)]
        if t and prev[key(n.x, n.y)] ~= "start" then
            -- at least 6 squares between the pump and the inlet (pipes, branch, valve, pipe)
            local len, k = 0, prev[key(n.x, n.y)]
            while k ~= "start" do len = len + 1; k = prev[k.k] end
            if len >= 7 then goal = n; break end
        end
        local start = prev[key(n.x, n.y)] == "start" and starts[key(n.x, n.y)]
        for j = 1, 4 do
            local x, y = n.x + SIDES[j][1], n.y + SIDES[j][2]
            local k = key(x, y)
            if (not withMeter or not start or start.out == j) and not prev[k] and math.abs(x - cx) <= r and math.abs(y - cy) <= r and (free(sq(x, y, 0)) or targets[k]) then
                prev[k] = { k = key(n.x, n.y), x = n.x, y = n.y }
                queue[#queue + 1] = { x = x, y = y }
            end
        end
    end
    if not goal then return nil, "no path from water to a building (fixtures " .. #fixtures .. ")" end
    local chain, k = { { x = goal.x, y = goal.y } }, prev[key(goal.x, goal.y)]
    while k ~= "start" do
        table.insert(chain, 1, { x = k.x, y = k.y })
        k = prev[k.k]
    end
    local target = targets[key(goal.x, goal.y)]
    local L = { pump = chain[1], inlet = chain[#chain], fixture = target.fixture, inletTurn = target.turn,
        pumpTurn = starts[key(chain[1].x, chain[1].y)].turn, pipes = {} }
    local used = {}
    for i = 1, #chain do used[key(chain[i].x, chain[i].y)] = true end
    for i = 2, #chain - 1 do L.pipes[#L.pipes + 1] = chain[i] end
    -- sprinkler beside one pipe (not the first, at least two pipes before the inlet), touching no other part;
    -- crop within 2; inline valve on a later pipe square with only its two chain neighbours; generator near the pump
    local branchIndex
    for i = 2, #L.pipes - 2 do
        local p = L.pipes[i]
        for j = 1, 4 do
            local x, y = p.x + SIDES[j][1], p.y + SIDES[j][2]
            if not L.sprinkler and not used[key(x, y)] and free(sq(x, y, 0)) and not nearWater(x, y)
                and not touchesAny(x, y, used, key(p.x, p.y)) then
                for dx = -2, 2 do
                    for dy = -2, 2 do
                        local qx, qy = x + dx, y + dy
                        if not L.crop and (dx ~= 0 or dy ~= 0) and dx * dx + dy * dy <= 4 and not used[key(qx, qy)]
                            and free(sq(qx, qy, 0)) and not hasWater(sq(qx, qy, 0)) then
                            L.sprinkler, L.crop, L.branch, branchIndex = { x = x, y = y }, { x = qx, y = qy }, p, i
                        end
                    end
                end
            end
        end
    end
    if not L.sprinkler then return nil, "no square for the sprinkler and the crop" end
    used[key(L.sprinkler.x, L.sprinkler.y)] = true
    for v = branchIndex + 1, #L.pipes - 1 do
        local p = L.pipes[v]
        local links = 0
        for j = 1, 4 do
            if used[key(p.x + SIDES[j][1], p.y + SIDES[j][2])] then links = links + 1 end
        end
        if not L.valve and links == 2 then
            L.valve = p
            table.remove(L.pipes, v)
        end
    end
    if not L.valve then return nil, "no square for the inline valve" end
    if withMeter then
        for v = #L.pipes - 1, 2, -1 do
            local p = L.pipes[v]
            local links = 0
            for j = 1, 4 do
                if used[key(p.x + SIDES[j][1], p.y + SIDES[j][2])] then links = links + 1 end
            end
            if not L.meter and links == 2 and not near(p, L.valve, 1) and not near(p, L.sprinkler, 1) then
                L.meter = p
                table.remove(L.pipes, v)
            end
        end
        if not L.meter then return nil, "no square for the flow meter" end
    end
    used[key(L.crop.x, L.crop.y)] = true
    for d = 2, 6 do
        for dx = -d, d do
            for dy = -d, d do
                local x, y = L.pump.x + dx, L.pump.y + dy
                if not L.gen and not used[key(x, y)] and free(sq(x, y, 0)) and not touchesAny(x, y, used) then
                    L.gen = { x = x, y = y }
                end
            end
        end
    end
    if not L.gen then return nil, "no square for the generator" end
    return L
end

local function describe(L)
    local f = L.fixture
    return "pump " .. key(L.pump.x, L.pump.y) .. " inlet " .. key(L.inlet.x, L.inlet.y) .. " pipes " .. #L.pipes
        .. " valve " .. key(L.valve.x, L.valve.y) .. (L.meter and (" meter " .. key(L.meter.x, L.meter.y)) or "")
        .. " sprinkler " .. key(L.sprinkler.x, L.sprinkler.y) .. " crop " .. key(L.crop.x, L.crop.y)
        .. " generator " .. key(L.gen.x, L.gen.y) .. " fixture " .. key(f.x, f.y) .. " "
        .. tostring(f.obj:getSpriteName())
end

-- ------------------------------------------------------------------ authority helpers

local function server()
    return LiveWater and LiveWater.Server
end

local function entryAt(p)
    local s = server()
    return s and s.topology:at(p.x, p.y, 0)
end

local function objectOf(p, typeId)
    local s = sq(p.x, p.y, 0)
    if not s then return nil end
    local objects = s:getObjects()
    for i = 0, objects:size() - 1 do
        local name = objects:get(i):getSpriteName()
        if name and LiveWater.Parts:typeOfSprite(name) == typeId then return objects:get(i) end
    end
    return nil
end

local function spriteOf(p, typeId)
    local s = sq(p.x, p.y, 0)
    if not s then return nil end
    local objects = s:getObjects()
    for i = 0, objects:size() - 1 do
        local name = objects:get(i):getSpriteName()
        if name and LiveWater.Parts:typeOfSprite(name) == typeId then return name end
    end
    return nil
end

local function giveItems(player, list)
    local inv = player:getInventory()
    for i = 1, #list do
        for _ = 1, list[i][2] do
            local item = instanceItem(list[i][1])
            if item then
                inv:AddItem(item)
                if isServer() then sendAddItemToContainer(inv, item) end
            end
        end
    end
end

-- Vanilla moveable placement (ISMoveablesAction:complete -> ISMoveableSpriteProps:placeMoveable): the props of
-- the facing set down (`spriteName`), the item found by its own sprite (`origName`, default the same), as a
-- rotated cursor does.
local function placeMoveable(player, spriteName, p, origName)
    local props = ISMoveableSpriteProps.new(getSprite(spriteName))
    local square = sq(p.x, p.y, 0)
    origName = origName or spriteName
    -- brush and low plants refuse a moveable (ISMoveableSpriteProps:isFreeTile, IsLow): the vegetation that
    -- `free` lets through is cleared first, as a player would
    if square then
        local objs = square:getObjects()
        for i = objs:size() - 1, 0, -1 do
            local o = objs:get(i)
            local name = o:getSpriteName() or ""
            if o ~= square:getFloor() and not string.find(name, "^vegetation_farming")
                and (string.find(name, "^e_") or string.find(name, "^vegetation_") or string.find(name, "^d_plants")) then
                square:transmitRemoveItemFromSquare(o)
            end
        end
    end
    -- nothing is set down under the player (vanilla refuses): step off the square first
    if math.floor(player:getX()) == p.x and math.floor(player:getY()) == p.y then
        player:teleportTo(p.x + 1.5, p.y + 1.5, 0)
    end
    local item = props:findInInventory(player, origName)
    if not item then return false, "moveable item not in inventory" end
    if not props:canPlaceMoveableInternal(player, square, item) then return false, "canPlaceMoveable refused" end
    props:placeMoveable(player, square, origName)
    return true
end

local function makeGenerator(p)
    local s = sq(p.x, p.y, 0)
    local gen = IsoGenerator.new(instanceItem("Base.Generator"), getCell(), s)
    local found = false
    local objects = s:getObjects()
    for i = 0, objects:size() - 1 do if objects:get(i) == gen then found = true end end
    if not found then s:AddSpecialObject(gen) end
    gen:setConnected(true)
    gen:setFuel(100)
    gen:setActivated(true)
    if isServer() then gen:transmitCompleteItemToClients() end
    return gen
end

local function plant(p)
    local system = SFarmingSystem.instance
    local s = sq(p.x, p.y, 0)
    system:plow(s)
    local plantObj = system:getLuaObjectAt(p.x, p.y, 0)
    if not plantObj then return nil end
    plantObj:seed("Carrots", 0)
    plantObj.waterLvl = 0
    plantObj:saveData()
    return plantObj
end

local function plantAt(p)
    return SFarmingSystem.instance:getLuaObjectAt(p.x, p.y, 0)
end

local function plumb(obj)
    obj:getModData().canBeWaterPiped = false
    obj:setUsesExternalWaterSource(true)
    obj:transmitModData()
    if isServer() then obj:sendObjectChange(IsoObjectChange.USES_EXTERNAL_WATER_SOURCE, { value = true }) end
end

local function expectedMask(L, p)
    local set = {}
    set[key(L.pump.x, L.pump.y)] = true
    set[key(L.inlet.x, L.inlet.y)] = true
    set[key(L.sprinkler.x, L.sprinkler.y)] = true
    set[key(L.valve.x, L.valve.y)] = true
    if L.meter then set[key(L.meter.x, L.meter.y)] = true end
    for i = 1, #L.pipes do set[key(L.pipes[i].x, L.pipes[i].y)] = true end
    local mask = 0
    for j = 1, 4 do
        if set[key(p.x + SIDES[j][1], p.y + SIDES[j][2])] then mask = mask + SIDES[j][3] end
    end
    return mask
end

-- Open (16 ew, 17 ns) or closed (18, 19) tile of the valve along its two chain neighbours.
local function valveIndex(L, open)
    local ew = false
    for j = 1, 4 do
        local x, y = L.valve.x + SIDES[j][1], L.valve.y + SIDES[j][2]
        local s = sq(x, y, 0)
        if SIDES[j][2] == 0 and s and (spriteOf({ x = x, y = y }, PIPE) or (x == L.inlet.x and y == L.inlet.y)
            or (x == L.pump.x and y == L.pump.y)) then ew = true end
    end
    return (open and 16 or 18) + (ew and 0 or 1)
end

-- Empty the relay tanks of the inlet (fixture: a dry house before the closed-valve phase).
local function drainRelays(L)
    local s = server()
    local list = s.relays:positions({ x = L.inlet.x, y = L.inlet.y, z = 0 })
    for i = 1, #list do
        local square = sq(list[i].x, list[i].y, list[i].z)
        local objects = square and square:getObjects()
        for j = 0, (objects and objects:size() or 0) - 1 do
            local obj = objects:get(j)
            if obj:hasModData() and obj:getModData().LiveWaterRelay and obj:getFluidContainer() then
                obj:getFluidContainer():Empty()
                obj:sync()
            end
        end
    end
end

local function relaysOf(L)
    local s = server()
    local list = s.relays:positions({ x = L.inlet.x, y = L.inlet.y, z = 0 })
    local amount, n = 0, 0
    for i = 1, #list do
        local r = s.relays.plumbing:relay(list[i].x, list[i].y, list[i].z)
        if r then
            n = n + 1
            amount = amount + r.amount
        end
    end
    return n, amount
end

-- Clean and tainted litres in the inlet's relay tanks. IsoObject.isTaintedWater of a plumbed fixture answers
-- false whenever its tank holds any fluid (Java 42.22 IsoObject.java:3004-3015): the tank's fluids are the proof.
local function relayFluids(L)
    local s = server()
    local list = s.relays:positions({ x = L.inlet.x, y = L.inlet.y, z = 0 })
    local clean, tainted = 0, 0
    for i = 1, #list do
        local square = sq(list[i].x, list[i].y, list[i].z)
        local objects = square and square:getObjects()
        for j = 0, (objects and objects:size() or 0) - 1 do
            local obj = objects:get(j)
            local fc = obj:hasModData() and obj:getModData().LiveWaterRelay and obj:getFluidContainer()
            if fc then
                clean = clean + fc:getSpecificFluidAmount(Fluid.Water)
                tainted = tainted + fc:getSpecificFluidAmount(Fluid.TaintedWater)
            end
        end
    end
    return clean, tainted
end

-- ------------------------------------------------------------------ the solo scenario

local S = {}

local function player()
    return getPlayer()
end

local function centersOf(text)
    local out = {}
    for x, y in string.gmatch(text or "", "(%d+),(%d+)") do out[#out + 1] = { x = tonumber(x), y = tonumber(y) } end
    return out
end

local function goNear(p)
    local pl = player()
    if near({ x = math.floor(pl:getX()), y = math.floor(pl:getY()) }, p, 2) and math.floor(pl:getZ()) == 0 then
        return
    end
    pl:teleportTo(p.x + 0.5, p.y + 0.5, 0)
end

local function send(command, args)
    sendClientCommand(player(), MODULE, command, args)
end

-- Count the real ten-minute steps of the game (same event as LWT_Server's clock).
-- What the step just done left (subscribed after LWT_Server, so it runs after the LiveWater clock): pump
-- running, outlet states, pump sprite, crop level. The checks of a phase read every step of that phase,
-- since a pump stops as soon as no outlet needs water (auto-stop) and an outlet then looks idle.
local function snapshot()
    local L = S.L
    if not (L and server()) then return end
    local pump, inlet, spr = entryAt(L.pump), entryAt(L.inlet), entryAt(L.sprinkler)
    local seen = S.seen
    local pd = pump and pump.data and pump.data.pump or {}
    if pd.running then seen.running = true end
    if pd.powered then seen.powered = true end
    local istate = inlet and inlet.data and inlet.data.outlet and inlet.data.outlet.state
    local sstate = spr and spr.data and spr.data.outlet and spr.data.outlet.state
    if istate then seen.inlet[istate] = true end
    if sstate then seen.sprinkler[sstate] = true end
    local ps = spriteOf(L.pump, "LiveWater:PondPump")
    if ps then seen.pumpSprite[ps] = true end
    -- Live Wire (optional): the watts it bills for the pump object this step
    local LW = rawget(_G, "LiveWire")
    if LW and LW.Consumption and LW.Consumers then
        local obj = objectOf(L.pump, "LiveWater:PondPump")
        if obj and LW.Consumers.of(obj) then
            seen.consumer = true
            local w = LW.Consumption.watts(obj) or 0
            if w > (seen.watts or 0) then seen.watts = w end
        end
    end
    seen.steps = seen.steps + 1
    seen.log[#seen.log + 1] = "step " .. seen.steps .. ": pump " .. tostring(pd.running) .. "/" .. tostring(pd.litres)
        .. " inlet " .. tostring(istate) .. " sprinkler " .. tostring(sstate) .. " sprite " .. tostring(ps)
end

local function resetSeen()
    S.seen = { inlet = {}, sprinkler = {}, pumpSprite = {}, steps = 0, log = {} }
end

local function seenText()
    return table.concat(S.seen.log, "; ")
end

local function onTen()
    S.tens = (S.tens or 0) + 1
    if S.seen then snapshot() end
end

local function waitSteps(n)
    return function()
        if not S.waitFrom then
            S.waitFrom = S.tens or 0
            resetSeen()
            setGameSpeed(3)
        end
        if (S.tens or 0) - S.waitFrom >= n then
            S.waitFrom = nil
            setGameSpeed(1)
            return true
        end
        return false
    end
end

-- ------------------------------------------------------------------ visual captures (param shots=1, E22)
-- Native screenshots for the wiki and the visual checks (autotest/scenarios/visual.json). The camera follows
-- the player (invisible), so a capture teleports the player onto the square to show, sets the zoom through
-- the public zoom controls, waits for the render, then calls takeScreenshot ("lwt-<name>.png", written to
-- the cache's Screenshots folder and copied into runs/... by pzdev). Right-click menus are opened with the
-- vanilla ISWorldObjectContextMenu.createMenu at the part's screen position (direct call, not a mouse
-- click); a hovered option is the menu's mouseOver index (its tooltip is then drawn by ISContextMenu).
-- Fixtures: noon and clear weather, the crop dried again before a capture block (so the sprinkler keeps
-- spraying), two vanilla rain collectors created as MORainCollectorBarrel does.

local function zoomTo(target)
    local core = getCore()
    core:setAutoZoom(0, false)
    local current = core:getNextZoom(0, 0)
    for _ = 1, 24 do
        local dir = target > current and 1 or -1
        local nextLevel = core:getNextZoom(0, dir)
        if math.abs(nextLevel - target) >= math.abs(current - target) then break end
        core:doZoomScroll(0, dir)
        current = nextLevel
    end
end

-- Hide the open windows (character panel, debug console...) for a capture; a scene capture also hides the HUD
-- (UIManager.setVisibleAllUI, what the vanilla "hide UI" key does), a menu capture keeps the UI layer for its menu.
local function hideWindows(scene)
    S.hiddenUI = {}
    local ui = UIManager.getUI()
    for i = 0, ui:size() - 1 do
        local w = ui:get(i)
        if w:isVisible() then
            S.hiddenUI[#S.hiddenUI + 1] = w
            w:setVisible(false)
        end
    end
    if scene then UIManager.setVisibleAllUI(false) end
end

local function restoreWindows()
    UIManager.setVisibleAllUI(true)
    for i = 1, #(S.hiddenUI or {}) do S.hiddenUI[i]:setVisible(true) end
    S.hiddenUI = nil
end

local function closeMenu()
    if S.menu then
        S.menu:hideToolTip()
        S.menu:closeAll()
        S.menu = nil
    end
end

-- Vanilla world menu of the objects on a square; `hover` (option text, optional) is shown hovered.
local function openMenu(p, objects, hover)
    local pn = player():getPlayerNum()
    local sx = isoToScreenX(pn, p.x + 0.5, p.y + 0.5, 0)
    local sy = isoToScreenY(pn, p.x + 0.5, p.y + 0.5, 0)
    local menu = ISWorldObjectContextMenu.createMenu(pn, objects, sx, sy)
    S.menu = menu
    if not (menu and hover) then return menu end
    for i = 1, #menu.options do
        if menu.options[i].name == hover then menu.mouseOver = i end
    end
    return menu
end

local function partMenu(p, typeId, hover)
    return function() openMenu(p(), { objectOf(p(), typeId) }, hover and getText(hover)) end
end

-- Attached jet frame of the sprinkler object (sprite name), or nil.
local function jetFrame(obj)
    local list = obj and obj:getAttachedAnimSprite()
    for i = 0, (list and list:size() or 0) - 1 do
        local sprite = list:get(i):getParentSprite()
        local name = sprite and sprite:getName()
        local index = name and tonumber(string.match(name, "^" .. SHEET .. "(%d+)$"))
        if index and index >= 80 and index <= 103 then return name end
    end
    return nil
end

local function jetModule()
    return require "LiveWater/LWT_SprinklerJet"
end

-- One capture: { name, at = function() -> {x, y}, zoom, prepare (after the camera settled), after, note,
-- again (optional: name of a second capture 250 ms later, two jet frames), offset (optional { dx, dy } of the
-- player, default { 1, 1 }) }. The player stands one square
-- south-east of the target (in front of it: the engine fades what stands in front of the player) and is drawn
-- fully transparent during the capture (alpha set at every poll).
local function shot(spec)
    addStep("screenshot " .. spec.name, function()
        local st = S.shot
        if not st or st.name ~= spec.name then
            S.shot = { name = spec.name, phase = 1, t = nowMs() }
            local p = spec.at()
            hideWindows(spec.prepare == nil)
            local off = spec.offset or { 1, 1 }
            player():teleportTo(p.x + off[1] + 0.5, p.y + off[2] + 0.5, 0)
            zoomTo(spec.zoomOf and spec.zoomOf() or spec.zoom or 0.5)
            return false
        end
        player():setAlphaAndTarget(0)
        if st.phase == 1 and nowMs() - st.t >= 3000 then
            if spec.prepare then spec.prepare() end
            st.phase, st.t = 2, nowMs()
        elseif st.phase == 2 and nowMs() - st.t >= 1500 then
            takeScreenshot("lwt-" .. spec.name .. ".png")
            info("screenshot lwt-" .. spec.name .. ".png" .. (spec.note and (" (" .. spec.note() .. ")") or ""))
            st.phase, st.t = spec.again and 25 or 3, nowMs()
        elseif st.phase == 25 and nowMs() - st.t >= 250 then
            takeScreenshot("lwt-" .. spec.again .. ".png")
            info("screenshot lwt-" .. spec.again .. ".png" .. (spec.note and (" (" .. spec.note() .. ")") or ""))
            st.phase, st.t = 3, nowMs()
        elseif st.phase == 3 and nowMs() - st.t >= 1000 then
            closeMenu()
            restoreWindows()
            player():setAlphaAndTarget(1)
            if spec.after then spec.after() end
            S.shot = nil
            return true
        end
        return false
    end, 30)
end

-- Fixture of a capture block: the crop is kept dry at every poll (the sprinkler keeps spraying and the pump
-- keeps running), from one ten-minute step before the captures until the end of the block.
local function keepDry()
    local pl = S.keepDry and S.L and plantAt(S.L.crop)
    if pl and pl.waterLvl > 0 then
        pl.waterLvl = 0
        pl:saveData()
    end
end

local function dryCrop()
    addStep("crop kept dry (fixture: the sprinkler keeps spraying)", function()
        S.keepDry = true
        keepDry()
        return true
    end)
    addStep("one ten-minute step with the crop dry", waitSteps(1), 120)
end

local function stopDry()
    addStep("crop no longer kept dry", function()
        S.keepDry = nil
        return true
    end)
end

local function at(field)
    return function() return S.L[field] end
end

local function middle()
    local L = S.L
    return L.pipes[math.floor(#L.pipes / 2) + 1]
end

local function spriteNote(field, typeId)
    return function() return tostring(spriteOf(S.L[field], typeId)) end
end

-- Jet frames read over real time (D08a): three reads about half a second apart, the module subscribed.
local function jetSteps()
    addStep("sprinkler jet changes frames over real time", function()
        local J = jetModule()
        local obj = objectOf(S.L.sprinkler, "LiveWater:Sprinkler")
        S.jet = S.jet or { reads = {} }
        local r = S.jet.reads
        local last = r[#r]
        if not last or nowMs() - last.t >= 500 then
            r[#r + 1] = { t = nowMs(), frame = jetFrame(obj), swaps = J.swaps }
        end
        if #r < 3 then return false end
        local changed = r[1].frame ~= r[2].frame and r[2].frame ~= r[3].frame
        local text = {}
        for i = 1, #r do text[i] = tostring(r[i].frame) .. "@" .. (r[i].t - r[1].t) .. "ms swaps " .. r[i].swaps end
        rec(J.ticking and J.count >= 1 and r[1].frame ~= nil and changed and r[3].swaps > r[1].swaps,
            "sprinkler jet changes frames over real time (OnTick subscribed)",
            "ticking " .. tostring(J.ticking) .. " count " .. J.count .. ": " .. table.concat(text, ", "))
        return true
    end, 10)
end

-- Vanilla rain collector entity on a square (as MORainCollectorBarrel creates one), with some water.
local function makeCollector(p, spriteName, litres)
    local s = sq(p.x, p.y, 0)
    local obj = IsoThumpable.new(getCell(), s, spriteName, false, {})
    obj:setBlockAllTheSquare(true)
    obj:setIsThumpable(true)
    local infoOf = SpriteConfigManager.getObjectInfoFromSprite(spriteName)
    if infoOf and infoOf:getScript() and infoOf:getScript():getParent() then
        GameEntityFactory.CreateIsoObjectEntity(obj, infoOf:getScript():getParent(), true)
    end
    s:AddSpecialObject(obj)
    local fc = obj:getFluidContainer()
    if fc then fc:addFluid(Fluid.Water, litres) end
    return obj, fc ~= nil
end

-- A free 3 x 3 block near the pump touching none of the layout's squares: two barrels on its first row,
-- two fittings (facing S: barrel behind them, pipe in front) on the second, three pipes on the third.
local function fittingArea(L)
    local used = {}
    local list = { L.pump, L.inlet, L.sprinkler, L.valve, L.crop, L.gen, L.meter }
    for i = 1, #L.pipes do list[#list + 1] = L.pipes[i] end
    for i = 1, #list do used[key(list[i].x, list[i].y)] = true end
    for d = 2, 12 do
        for dx = -d, d do
            for dy = -d, d do
                local x0, y0 = L.pump.x + dx, L.pump.y + dy
                local ok = true
                for i = 0, 2 do
                    for j = 0, 2 do
                        local x, y = x0 + i, y0 + j
                        if ok and (used[key(x, y)] or touchesAny(x, y, used) or not free(sq(x, y, 0))
                            or nearWater(x, y)) then ok = false end
                    end
                end
                if ok then return { x = x0, y = y0 } end
            end
        end
    end
    return nil
end

local function fittingSteps()
    local FIT = "LiveWater:BarrelFitting"
    addStep("barrel fittings: area, rain collectors, pipes, fittings", function()
        local F = S.F
        if not F then
            local a = fittingArea(S.L)
            if not a then
                rec(false, "barrel fitting area found near the pump")
                return "abort"
            end
            local _, tall = makeCollector({ x = a.x, y = a.y }, "carpentry_02_122", 120)
            local _, low = makeCollector({ x = a.x + 2, y = a.y }, "carpentry_02_54", 80)
            rec(tall and low, "vanilla rain collectors set (fixture)", "round barrel " .. key(a.x, a.y)
                .. ", crate " .. key(a.x + 2, a.y))
            S.F = { a = a, tall = { x = a.x, y = a.y + 1 }, low = { x = a.x + 2, y = a.y + 1 }, i = 0,
                pipes = { { x = a.x, y = a.y + 2 }, { x = a.x + 1, y = a.y + 2 }, { x = a.x + 2, y = a.y + 2 } } }
            return false
        end
        local p = F.pipes[F.i]
        if p and not entryAt(p) then return false end
        F.i = F.i + 1
        local nextPipe = F.pipes[F.i]
        if nextPipe then
            goNear(nextPipe)
            send("lay", { x = nextPipe.x, y = nextPipe.y, z = 0, part = PIPE })
            return false
        end
        goNear(F.tall)
        local ok1, why1 = placeMoveable(player(), FITTING_SPRITE, F.tall)
        local ok2, why2 = placeMoveable(player(), FITTING_SPRITE, F.low)
        rec(ok1 and ok2 and entryAt(F.tall) ~= nil and entryAt(F.low) ~= nil,
            "two barrel fittings set down (vanilla placement)", tostring(why1 or "") .. " " .. tostring(why2 or ""))
        return true
    end, 60)
    addStep("one ten-minute step for the fittings", waitSteps(1), 120)
    addStep("fitting drawn by its container's shape", function()
        local F = S.F
        local tall, low = spriteOf(F.tall, FIT), spriteOf(F.low, FIT)
        rec(tall == SHEET .. "64" and low == SHEET .. "68", "fitting drawn by its container's shape (Fill)",
            "round barrel " .. tostring(tall) .. ", crate " .. tostring(low))
        return true
    end)
    shot({ name = "barrel-fittings", at = function() return { x = S.F.a.x + 1, y = S.F.a.y + 1 } end })
    shot({ name = "menu-fitting-info", at = function() return S.F.low end,
        prepare = function() openMenu(S.F.low, { objectOf(S.F.low, FIT) }, getText("ContextMenu_LWT_Info")) end })
end

-- Showcase (promotional picture, every part in one frame): on the working installation, a branch from one
-- pipe to a barrel fitting on a vanilla rain collector (Fill), and an automatic sprinkler beside another pipe
-- with its own crop, opened by hand (switchValve). Squares: free, touching no other part than their pipe.
local FIT_FACING = { { 0, -1, 64 }, { -1, 0, 65 }, { 0, 1, 66 }, { 1, 0, 67 } }   -- branch direction -> fitting

local function showcaseSquares(L)
    local used = {}
    local list = { L.pump, L.inlet, L.sprinkler, L.valve, L.crop, L.gen, L.meter }
    for i = 1, #L.pipes do list[#list + 1] = L.pipes[i] end
    for i = 1, #list do used[key(list[i].x, list[i].y)] = true end
    local function ok(x, y, except)
        return not used[key(x, y)] and free(sq(x, y, 0)) and not nearWater(x, y) and not touchesAny(x, y, used, except)
    end
    -- pipes from the middle of the line outwards, away from the other parts
    local order, mid = {}, math.floor(#L.pipes / 2) + 1
    for d = 0, #L.pipes do
        for _, i in ipairs({ mid - d, mid + d }) do
            local p = L.pipes[i]
            if p and not order[key(p.x, p.y)] and not near(p, L.valve, 1) and not near(p, L.sprinkler, 1)
                and not (L.meter and near(p, L.meter, 1)) and not near(p, L.inlet, 2) and not near(p, L.pump, 2) then
                order[key(p.x, p.y)] = true
                order[#order + 1] = p
            end
        end
    end
    -- the automatic sprinkler and its crop on natural ground (not a paved terrace)
    local function soil(x, y)
        local s = sq(x, y, 0)
        local floor = s and s:getFloor()
        return floor ~= nil and string.find(floor:getSpriteName() or "", "^blends_natural") ~= nil
    end
    local X = {}
    -- the line's middle pipes first, then any pipe of the line
    local all = {}
    for i = 1, #order do all[#all + 1] = order[i] end
    for i = 1, #L.pipes do all[#all + 1] = L.pipes[i] end
    for i = 1, #all do
        local p = all[i]
        for f = 1, #FIT_FACING do
            local dx, dy = FIT_FACING[f][1], FIT_FACING[f][2]
            local b1, b2, b3 = { x = p.x + dx, y = p.y + dy }, { x = p.x + 2 * dx, y = p.y + 2 * dy },
                { x = p.x + 3 * dx, y = p.y + 3 * dy }
            -- the barrel is no part: only free and off the water
            if not X.fitting and ok(b1.x, b1.y, key(p.x, p.y)) and ok(b2.x, b2.y, key(b1.x, b1.y))
                and not used[key(b3.x, b3.y)] and free(sq(b3.x, b3.y, 0)) and not hasWater(sq(b3.x, b3.y, 0)) then
                X.tee, X.pipe, X.fitting, X.barrel, X.fitSprite = p, b1, b2, b3, SHEET .. FIT_FACING[f][3]
                used[key(b1.x, b1.y)], used[key(b2.x, b2.y)], used[key(b3.x, b3.y)] = true, true, true
            end
        end
    end
    if not X.fitting then return nil, "no square for the barrel branch" end
    -- automatic sprinkler: beside any pipe of the line but the tee, or at the end of one more pipe; with a crop
    -- square around it; on natural ground first, then anywhere free
    local function cropAround(x, y, natural)
        for dx = -1, 1 do
            for dy = -1, 1 do
                local qx, qy = x + dx, y + dy
                if (dx ~= 0 or dy ~= 0) and not used[key(qx, qy)] and free(sq(qx, qy, 0))
                    and (not natural or soil(qx, qy)) then
                    return { x = qx, y = qy }
                end
            end
        end
        return nil
    end
    for pass = 1, 2 do
        local natural = pass == 1
        for reach = 1, 2 do
            for i = 1, #L.pipes do
                local p = L.pipes[i]
                if not X.auto and not (p.x == X.tee.x and p.y == X.tee.y) then
                    for j = 1, 4 do
                        local dx, dy = SIDES[j][1], SIDES[j][2]
                        local b1, b2 = { x = p.x + dx, y = p.y + dy }, { x = p.x + 2 * dx, y = p.y + 2 * dy }
                        local spot, link = b1, nil
                        if reach == 2 then spot, link = b2, b1 end
                        local fits = not X.auto and (natural == false or soil(spot.x, spot.y))
                        if fits and link then
                            fits = ok(link.x, link.y, key(p.x, p.y)) and ok(spot.x, spot.y, key(link.x, link.y))
                        elseif fits then
                            fits = ok(spot.x, spot.y, key(p.x, p.y))
                        end
                        local crop = fits and cropAround(spot.x, spot.y, natural)
                        if crop then X.auto, X.autoPipe, X.autoCrop = spot, link, crop end
                    end
                end
            end
        end
    end
    if not X.auto then return nil, "no square for the automatic sprinkler" end
    return X
end

-- Square at the centre of every part of the showcase and the zoom that fits them in a 1280 x 720 picture
-- (at zoom 1 a step along x - y is 32 px across, a step along x + y 16 px down; margins kept).
local function showcaseFrame()
    local L, X = S.L, S.X
    local list = { L.pump, L.gen, L.inlet, L.sprinkler, L.valve, L.meter, X.barrel, X.fitting, X.auto }
    local a1, a2, b1, b2
    for i = 1, #list do
        local p = list[i]
        if p then
            local a, b = p.x - p.y, p.x + p.y
            a1, a2 = math.min(a1 or a, a), math.max(a2 or a, a)
            b1, b2 = math.min(b1 or b, b), math.max(b2 or b, b)
        end
    end
    -- the view centres a little above the player's square: one step further down the screen
    local a, b = (a1 + a2) / 2, (b1 + b2) / 2 + 2
    local x, y = math.floor((a + b) / 2 + 0.5), math.floor((b - a) / 2 + 0.5)
    local zoom = math.max(0.75, (a2 - a1 + 6) * 32 / 1280, (b2 - b1 + 10) * 16 / 720)
    return { x = x, y = y }, zoom
end

local function showcaseSteps()
    local FIT, AUTO = "LiveWater:BarrelFitting", "LiveWater:SprinklerAuto"
    addStep("showcase: barrel branch laid", function()
        if not S.X then
            local X, why = showcaseSquares(S.L)
            if not X then
                rec(false, "showcase squares found", why)
                return "abort"
            end
            S.X = X
            info("showcase: tee " .. key(X.tee.x, X.tee.y) .. " fitting " .. key(X.fitting.x, X.fitting.y)
                .. " barrel " .. key(X.barrel.x, X.barrel.y) .. " auto sprinkler " .. key(X.auto.x, X.auto.y))
            goNear(X.pipe)
            send("lay", { x = X.pipe.x, y = X.pipe.y, z = 0, part = PIPE })
            return false
        end
        local X = S.X
        if not entryAt(X.pipe) then return false end
        if not X.autoPipe then return true end
        if not X.autoPipeSent then
            X.autoPipeSent = true
            goNear(X.autoPipe)
            send("lay", { x = X.autoPipe.x, y = X.autoPipe.y, z = 0, part = PIPE })
            return false
        end
        return entryAt(X.autoPipe) ~= nil
    end, 30)
    addStep("showcase: rain collector, fitting, automatic sprinkler, crop", function()
        local X = S.X
        if not X.placed then
            X.placed = true
            -- nearly full: the fitting takes a few litres, the pump's flow is left for the sprinklers
            local barrel, hasFluid = makeCollector(X.barrel, "carpentry_02_122", 0)
            local fc = barrel:getFluidContainer()
            if fc then fc:addFluid(Fluid.Water, math.max(0, fc:getFreeCapacity() - 5)) end
            goNear(X.fitting)
            local ok1, why1 = placeMoveable(player(), X.fitSprite, X.fitting, FITTING_SPRITE)
            goNear(X.auto)
            local ok2, why2 = placeMoveable(player(), SHEET .. "56", X.auto)
            local crop = plant(X.autoCrop)
            if crop then
                crop.waterLvl = 0
                crop:saveData()
            end
            rec(hasFluid and ok1 and ok2 and crop ~= nil, "showcase parts set down (vanilla placement)",
                tostring(why1 or "") .. " " .. tostring(why2 or ""))
            send("switchValve", { x = X.auto.x, y = X.auto.y, z = 0 })
            return false
        end
        local e = entryAt(X.auto)
        return e ~= nil and e.data and e.data.valve and e.data.valve.open == true
    end, 30)
    addStep("one ten-minute step for the showcase", waitSteps(1), 120)
    addStep("showcase: fitting filling, automatic sprinkler watering", function()
        local X = S.X
        local fit, auto = spriteOf(X.fitting, FIT), spriteOf(X.auto, AUTO)
        local idx = auto and tonumber(string.sub(auto, #SHEET + 1)) or -1
        rec(fit ~= nil and idx >= 60 and idx <= 63, "showcase: fitting drawn, automatic sprinkler watering",
            "fitting " .. tostring(fit) .. ", automatic sprinkler " .. tostring(auto))
        return true
    end)
end

-- Visual captures: the house inlet hangs on the south wall of its house (house north of it, wallNorth): the
-- player waits outside, south-east of it.
local OUTSIDE = { 1, 1 }

local function visualSteps(block)
    if block == "unfiltered" then
        dryCrop()
        shot({ name = "network-unfiltered", at = at("valve"), zoom = 0.75 })
        shot({ name = "pump-running", at = at("pump"), note = spriteNote("pump", "LiveWater:PondPump") })
        shot({ name = "inlet-unfiltered", at = at("inlet"), offset = OUTSIDE, note = spriteNote("inlet", "LiveWater:HouseInlet") })
        jetSteps()
        local jetNote = function() return tostring(jetFrame(objectOf(S.L.sprinkler, "LiveWater:Sprinkler"))) end
        shot({ name = "sprinkler-jet-a", again = "sprinkler-jet-b", at = at("sprinkler"), note = jetNote })
        shot({ name = "valve-open", at = at("valve"), note = spriteNote("valve", VALVE) })
        shot({ name = "flow-meter", at = at("meter"), note = spriteNote("meter", "LiveWater:FlowMeter") })
        shot({ name = "menu-pump-info", at = at("pump"),
            prepare = partMenu(at("pump"), "LiveWater:PondPump", "ContextMenu_LWT_Info") })
        shot({ name = "menu-valve", at = at("valve"), prepare = partMenu(at("valve"), VALVE) })
        addStep("network view asked (showNetwork)", function()
            local View = require "LiveWater/LWT_NetworkView"
            if not S.viewSent then
                S.viewSent = true
                goNear(S.L.pump)
                send("showNetwork", { x = S.L.pump.x, y = S.L.pump.y, z = 0 })
                return false
            end
            if #View.shown == 0 then return false end
            rec(true, "network view highlights the parts", #View.shown .. " parts")
            return true
        end, 20)
        shot({ name = "network-view", at = middle, zoom = 1.0 })
        shot({ name = "menu-network-legend", at = at("inlet"), offset = OUTSIDE,
            prepare = partMenu(at("inlet"), "LiveWater:HouseInlet", "ContextMenu_LWT_HideNetwork"),
            after = function() (require "LiveWater/LWT_NetworkView").clear() end })
        stopDry()
    elseif block == "filtered" then
        dryCrop()
        shot({ name = "pump-filter-running", at = at("pump"), note = spriteNote("pump", "LiveWater:PondPump") })
        shot({ name = "inlet-filtered", at = at("inlet"), offset = OUTSIDE, note = spriteNote("inlet", "LiveWater:HouseInlet") })
        shot({ name = "network-filtered", at = at("valve"), zoom = 0.75 })
        -- whole installation working (pump, filter, line, valve, meter, sprinkler spraying, house served, plus the
        -- showcase: barrel branch and automatic sprinkler), for
        -- a promotional picture: the trees around it are removed from this copied world (their faded outlines
        -- would cover the parts).
        addStep("staging: trees around the installation removed", function()
            local L, n = S.L, 0
            local x1, x2 = math.min(L.pump.x, L.inlet.x) - 10, math.max(L.pump.x, L.inlet.x) + 10
            local y1, y2 = math.min(L.pump.y, L.inlet.y) - 10, math.max(L.pump.y, L.inlet.y) + 10
            for x = x1, x2 do
                for y = y1, y2 do
                    local s = sq(x, y, 0)
                    local objs = s and s:getObjects()
                    for i = (objs and objs:size() or 0) - 1, 0, -1 do
                        local o = objs:get(i)
                        if instanceof(o, "IsoTree") then
                            s:transmitRemoveItemFromSquare(o)
                            n = n + 1
                        end
                    end
                end
            end
            info("staging: " .. n .. " tree(s) removed")
            return true
        end)
        showcaseSteps()
        shot({ name = "installation", at = middle, zoom = 1.0 })
        shot({ name = "installation-close", at = at("valve"), zoom = 0.75 })
        addStep("showcase framed", function()
            -- staging: the bushes on the parts' squares and on the squares in front of them (south, east) would
            -- hide the pipes; removed from this copied world (crops kept)
            local L, X, n = S.L, S.X, 0
            local list = { L.pump, L.inlet, L.sprinkler, L.valve, L.meter, X.pipe, X.fitting, X.auto, X.autoPipe }
            for i = 1, #L.pipes do list[#list + 1] = L.pipes[i] end
            for i = 1, #list do
                local p = list[i]
                for _, d in ipairs({ { 0, 0 }, { 1, 0 }, { 0, 1 }, { 1, 1 } }) do
                    local s = p and sq(p.x + d[1], p.y + d[2], 0)
                    local objs = s and s:getObjects()
                    for k = (objs and objs:size() or 0) - 1, 0, -1 do
                        local o = objs:get(k)
                        local name = o:getSpriteName() or ""
                        if o ~= s:getFloor() and not string.find(name, "^vegetation_farming")
                            and (string.find(name, "^vegetation_") or string.find(name, "^f_bushes")) then
                            s:transmitRemoveItemFromSquare(o)
                            n = n + 1
                        end
                    end
                end
            end
            info("staging: " .. n .. " bush(es) removed")
            local c, zoom = showcaseFrame()
            S.showcaseAt, S.showcaseZoom = c, zoom
            info("showcase frame " .. key(c.x, c.y) .. " zoom " .. zoom)
            return true
        end)
        shot({ name = "showcase", at = function() return S.showcaseAt end, offset = { 0, 0 },
            zoomOf = function() return S.showcaseZoom end })
        -- the later phases are judged on the nominal network alone
        addStep("showcase: branch pipe taken up and automatic sprinkler closed", function()
            local X = S.X
            if not X.undone then
                X.undone = true
                goNear(X.pipe)
                send("dismantle", { x = X.pipe.x, y = X.pipe.y, z = 0 })
                return false
            end
            if entryAt(X.pipe) then return false end
            if not X.closing then
                X.closing = true
                goNear(X.auto)
                send("switchValve", { x = X.auto.x, y = X.auto.y, z = 0 })
                return false
            end
            local e = entryAt(X.auto)
            if entryAt(X.pipe) or not (e and e.data and e.data.valve and e.data.valve.open == false) then
                return false
            end
            rec(true, "showcase undone (branch pipe taken up, automatic sprinkler closed)")
            return true
        end, 30)
        stopDry()
    elseif block == "inline closed" then
        shot({ name = "valve-closed", at = at("valve"), note = spriteNote("valve", VALVE) })
        shot({ name = "menu-sink-dry", at = function() return S.L.fixture end,
            prepare = function() openMenu(S.L.fixture, { S.L.fixture.obj }) end })
    elseif block == "sprinkler closed" then
        addStep("jet stopped and unsubscribed with the sprinkler closed", function()
            local J = jetModule()
            local frame = jetFrame(objectOf(S.L.sprinkler, "LiveWater:Sprinkler"))
            rec(J.count == 0 and not J.ticking and frame == nil, "jet module unsubscribed once the sprinkler stops",
                "count " .. J.count .. " ticking " .. tostring(J.ticking) .. " frame " .. tostring(frame))
            return true
        end)
        shot({ name = "sprinkler-closed", at = at("sprinkler"), note = spriteNote("sprinkler", "LiveWater:Sprinkler") })
        fittingSteps()
    end
end

local function buildSteps(ctx)
    local P = ctx.params or {}
    local radius = tonumber(P.radius) or 40
    local stepSec = tonumber(P.stepSec) or 90
    local centers = centersOf(P.centers)
    local visual = P.shots == "1"
    S.centerIndex = 0

    addStep("player untouchable and items given", function()
        local pl = player()
        pl:setGodMod(true)
        pl:setInvisible(true)
        giveItems(pl, { { "LiveWater.PipeSection", 80 }, { "LiveWater.WaterFilter", 1 }, { "Base.PipeWrench", 1 },
            { "Base.Mov_LiveWater_PondPump", 1 }, { "Base.Mov_LiveWater_HouseInlet", 1 },
            { "Base.Mov_LiveWater_Sprinkler", 1 }, { "Base.Mov_LiveWater_Valve", 1 } })
        if visual then
            giveItems(pl, { { "Base.Mov_LiveWater_FlowMeter", 1 }, { "Base.Mov_LiveWater_BarrelFitting", 3 },
                { "Base.Mov_LiveWater_SprinklerAuto", 1 } })
            getGameTime():setTimeOfDay(11)
            getClimateManager():stopWeatherAndThunder()
            info("visual fixtures: 11:00, weather stopped")
        end
        rec(server() ~= nil, "LiveWater authority built (LiveWater.Server)")
        Events.EveryTenMinutes.Add(onTen)
        return true
    end)

    addStep("layout found near water", function()
        if not S.center then
            S.centerIndex = S.centerIndex + 1
            S.center = centers[S.centerIndex]
            if not S.center and S.best and not S.bestDone then
                -- the last places had no layout: go back to the best one
                S.bestDone = true
                S.centerIndex = S.best.index
                S.center = centers[S.centerIndex]
            end
            if not S.center then
                rec(false, "layout found near water", "no candidate place left")
                return "abort"
            end
            player():teleportTo(S.center.x + 0.5, S.center.y + 0.5, 0)
            S.teleportedAt = nowMs()
            return false
        end
        if nowMs() - S.teleportedAt < 6000 then return false end
        local c = S.center
        if not (sq(c.x - radius, c.y - radius, 0) and sq(c.x + radius, c.y + radius, 0)) then
            if nowMs() - S.teleportedAt < 40000 then return false end
        end
        local L, why = findLayout(c.x, c.y, radius, visual)
        if not L then
            info("no layout around " .. key(c.x, c.y) .. ": " .. tostring(why))
            S.center = nil
            return false
        end
        -- visual captures: the shortest line of all the candidate places (the whole installation in one
        -- picture); every place is tried, then the best one is searched again once loaded around the player
        if visual and not S.bestDone then
            info("layout around " .. key(c.x, c.y) .. ": " .. #L.pipes .. " pipes")
            if not S.best or #L.pipes < S.best.n then S.best = { n = #L.pipes, index = S.centerIndex } end
            if S.centerIndex < #centers then
                S.center = nil
                return false
            end
            S.bestDone = true
            if S.best.index ~= S.centerIndex then
                S.centerIndex = S.best.index - 1
                S.center = nil
                return false
            end
        end
        S.L = L
        rec(true, "layout found near water", "around " .. key(c.x, c.y) .. ": " .. describe(L))
        return true
    end, 600)

    addStep("fixtures: generator, crop, plumbed fixture", function()
        local L = S.L
        S.gen = makeGenerator(L.gen)
        local plantObj = plant(L.crop)
        plumb(L.fixture.obj)
        rec(S.gen ~= nil and S.gen:isActivated(), "generator on next to the pump", key(L.gen.x, L.gen.y))
        rec(plantObj ~= nil and plantObj.state == "seeded", "carrot crop seeded",
            plantObj and ("state " .. tostring(plantObj.state) .. " needed " .. tostring(plantObj.waterNeeded)))
        rec(L.fixture.obj:getUsesExternalWaterSource(), "fixture plumbed", tostring(L.fixture.obj:getSpriteName()))
        return true
    end)

    addStep("pond pump set down next to water (vanilla placement)", function()
        goNear(S.L.pump)
        local ok, why = placeMoveable(player(), SHEET .. (24 + (S.L.pumpTurn or 0)), S.L.pump, PUMP_SPRITE)
        local e = entryAt(S.L.pump)
        rec(ok and e ~= nil and e.type == "LiveWater:PondPump", "pond pump set down next to water (vanilla placement)",
            tostring(why or "") .. " entry " .. tostring(e and e.type) .. " source "
            .. tostring(e and e.data and e.data.intake and e.data.intake.source))
        return true
    end)

    addStep("pipes laid through the lay command", function()
        local L = S.L
        S.pipeIndex = S.pipeIndex or 0
        local p = L.pipes[S.pipeIndex]
        if p and not entryAt(p) then return false end
        S.pipeIndex = S.pipeIndex + 1
        local nextPipe = L.pipes[S.pipeIndex]
        if not nextPipe then
            rec(true, "pipes laid through the lay command", #L.pipes .. " pipes")
            return true
        end
        goNear(nextPipe)
        send("lay", { x = nextPipe.x, y = nextPipe.y, z = 0, part = PIPE })
        return false
    end, 120)

    addStep("house inlet and sprinkler set down (vanilla placement)", function()
        local L = S.L
        goNear(L.inlet)
        local ok1, why1 = placeMoveable(player(), SHEET .. (40 + (L.inletTurn or 0)), L.inlet, INLET_SPRITE)
        goNear(L.sprinkler)
        local ok2, why2 = placeMoveable(player(), SPRINKLER_SPRITE, L.sprinkler)
        goNear(L.valve)
        local ok3, why3 = placeMoveable(player(), VALVE_SPRITE, L.valve)
        if L.meter then
            goNear(L.meter)
            local ok4, why4 = placeMoveable(player(), METER_SPRITE, L.meter)
            local e4 = entryAt(L.meter)
            rec(ok4 and e4 ~= nil, "flow meter set down between two pipes", tostring(why4 or "") .. " "
                .. tostring(e4 and e4.type))
        end
        local e3 = entryAt(L.valve)
        rec(ok3 and e3 ~= nil and e3.type == VALVE, "inline valve set down between two pipes",
            tostring(why3 or "") .. " " .. tostring(e3 and e3.type))
        local e1, e2 = entryAt(L.inlet), entryAt(L.sprinkler)
        rec(ok1 and e1 ~= nil, "house inlet set down against the house", tostring(why1 or "") .. " "
            .. tostring(e1 and e1.type))
        rec(ok2 and e2 ~= nil, "manual sprinkler set down by the branch", tostring(why2 or "") .. " "
            .. tostring(e2 and e2.type))
        return true
    end)

    addStep("network built with sprites by side mask", function()
        local L, s = S.L, server()
        local id = s.network:networkAt(L.pump.x, L.pump.y, 0)
        local all = { L.inlet, L.sprinkler, L.valve, L.meter }
        for i = 1, #L.pipes do all[#all + 1] = L.pipes[i] end
        local apart = 0
        for i = 1, #all do
            if s.network:networkAt(all[i].x, all[i].y, 0) ~= id then apart = apart + 1 end
        end
        rec(id ~= nil and apart == 0, "one network from the pump to the inlet and the sprinkler",
            "network " .. tostring(id) .. ", parts outside " .. apart .. ", members " .. #s.network:members(id or -1))
        local wrong = {}
        for i = 1, #L.pipes do
            local p = L.pipes[i]
            local want = SHEET .. expectedMask(L, p)
            local got = spriteOf(p, PIPE)
            if got ~= want then wrong[#wrong + 1] = key(p.x, p.y) .. " " .. tostring(got) .. "~=" .. want end
        end
        rec(#wrong == 0, "pipe sprites follow their side masks", #wrong == 0 and (#L.pipes .. " pipes")
            or table.concat(wrong, "; "))
        local vs = spriteOf(L.valve, VALVE)
        rec(vs == SHEET .. valveIndex(L, true), "inline valve drawn open along its pipe", tostring(vs))
        return true
    end)

    addStep("sprinkler valve opened (switchValve)", function()
        local e = entryAt(S.L.sprinkler)
        if not S.valveSent then
            S.valveSent = true
            goNear(S.L.sprinkler)
            send("switchValve", { x = S.L.sprinkler.x, y = S.L.sprinkler.y, z = 0 })
            return false
        end
        if not (e and e.data and e.data.valve and e.data.valve.open == true) then return false end
        rec(true, "sprinkler valve opened (switchValve)")
        local pl = plantAt(S.L.crop)
        S.levelBefore = pl and pl.waterLvl or -1
        goNear(S.L.pump)
        return true
    end, 20)

    addStep("two ten-minute steps without filter", waitSteps(2), stepSec * 2)

    addStep("checks without filter", function()
        local L, seen = S.L, S.seen
        info(seenText())
        rec(seen.powered and seen.running and seen.pumpSprite[SHEET .. (28 + (L.pumpTurn or 0))] == true,
            "pump powered by the generator, running, sprite on")
        if P.livewire == "1" then
            rec(seen.consumer == true and (seen.watts or 0) > 0, "Live Wire knows the pump as a consumer and bills it",
                "watts " .. tostring(seen.watts))
        end
        local n, amount = relaysOf(L)
        local isprite = spriteOf(L.inlet, "LiveWater:HouseInlet")
        rec(seen.inlet.unfiltered and not seen.inlet.served and amount <= 0.001,
            "house inlet refuses unfiltered pond water", "relays " .. n .. " litres " .. amount)
        rec(isprite == SHEET .. (44 + (L.inletTurn or 0)), "house inlet sprite amber (unfiltered)", tostring(isprite))
        local pl = plantAt(L.crop)
        local level = pl and pl.waterLvl or -1
        rec(seen.sprinkler.served and level > S.levelBefore, "sprinkler waters the crop",
            "water level " .. tostring(S.levelBefore) .. " -> " .. tostring(level))
        return true
    end)

    if visual then visualSteps("unfiltered") end

    addStep("filter fitted (fitFilter)", function()
        local pump = entryAt(S.L.pump)
        if not S.filterSent then
            S.filterSent = true
            goNear(S.L.pump)
            send("fitFilter", { x = S.L.pump.x, y = S.L.pump.y, z = 0 })
            return false
        end
        local f = pump and pump.data and pump.data.filter
        if not (f and f.fitted == true) then return false end
        rec(true, "filter fitted (fitFilter)", "capacity " .. tostring(f.capacity) .. " L")
        return true
    end, 20)

    addStep("two ten-minute steps with filter", waitSteps(2), stepSec * 2)

    addStep("checks with filter", function()
        local L, seen = S.L, S.seen
        info(seenText())
        local n, amount = relaysOf(L)
        rec(seen.inlet.served and n > 0 and amount > 0, "house inlet served, relay tank filled",
            "relays " .. n .. " litres " .. amount)
        local isprite = spriteOf(L.inlet, "LiveWater:HouseInlet")
        rec(isprite == SHEET .. (40 + (L.inletTurn or 0)), "house inlet sprite green (filtered)", tostring(isprite))
        local obj = L.fixture.obj
        local clean, tainted = relayFluids(L)
        rec(obj:getFluidAmount() > 0 and obj:hasWater() and clean > 0 and tainted <= 0.001,
            "the plumbed fixture gives clean water", "fixture litres " .. tostring(obj:getFluidAmount())
            .. ", tank clean " .. clean .. " tainted " .. tainted)
        rec(seen.pumpSprite[SHEET .. (32 + (L.pumpTurn or 0))] == true, "pump sprite running with filter")
        return true
    end)

    if visual then visualSteps("filtered") end

    addStep("inline valve closed (switchValve)", function()
        local e = entryAt(S.L.valve)
        if not S.inlineSent then
            S.inlineSent = true
            goNear(S.L.valve)
            send("switchValve", { x = S.L.valve.x, y = S.L.valve.y, z = 0 })
            return false
        end
        if not (e and e.data and e.data.valve and e.data.valve.open == false) then return false end
        drainRelays(S.L)
        local pl = plantAt(S.L.crop)
        pl.waterLvl = 0
        pl:saveData()
        rec(true, "inline valve closed (switchValve)", "relays emptied, crop dry (fixture)")
        goNear(S.L.pump)
        return true
    end, 20)

    addStep("two ten-minute steps with the inline valve closed", waitSteps(2), stepSec * 2)

    addStep("checks with the inline valve closed", function()
        local L, seen = S.L, S.seen
        info(seenText())
        local n, amount = relaysOf(L)
        rec(not seen.inlet.served and amount <= 0.001, "closed inline valve stops the house inlet downstream",
            "relays " .. n .. " litres " .. amount)
        local pl = plantAt(L.crop)
        rec(seen.sprinkler.served and pl and pl.waterLvl > 0, "the sprinkler upstream of the valve still waters",
            "level " .. tostring(pl and pl.waterLvl))
        local vs = spriteOf(L.valve, VALVE)
        rec(vs == SHEET .. valveIndex(L, false), "inline valve drawn closed", tostring(vs))
        return true
    end)

    if visual then visualSteps("inline closed") end

    addStep("sprinkler valve closed (switchValve)", function()
        local e = entryAt(S.L.sprinkler)
        if not S.closeSent then
            S.closeSent = true
            goNear(S.L.sprinkler)
            send("switchValve", { x = S.L.sprinkler.x, y = S.L.sprinkler.y, z = 0 })
            return false
        end
        if not (e and e.data and e.data.valve and e.data.valve.open == false) then return false end
        local pl = plantAt(S.L.crop)
        pl.waterLvl = 0
        pl:saveData()
        S.levelClosed = 0
        rec(true, "sprinkler valve closed (switchValve)")
        goNear(S.L.pump)
        return true
    end, 20)

    addStep("two ten-minute steps with the valve closed", waitSteps(2), stepSec * 2)

    addStep("checks with the valve closed", function()
        local L = S.L
        local spr = entryAt(L.sprinkler)
        local sstate = spr and spr.data and spr.data.outlet and spr.data.outlet.state
        local pl = plantAt(L.crop)
        local level = pl and pl.waterLvl or -1
        info(seenText())
        rec(sstate == "closed" and not S.seen.sprinkler.served and level <= S.levelClosed,
            "closed valve stops the sprinkler branch", "state " .. tostring(sstate) .. " water level " .. tostring(level))
        return true
    end)

    if visual then visualSteps("sprinkler closed") end

    addStep("no Lua error recorded", function()
        local n = getLuaDebuggerErrorCount and getLuaDebuggerErrorCount() or 0
        rec(n == 0, "no Lua error recorded", "errors=" .. tostring(n))
        return true
    end)
end

-- ------------------------------------------------------------------ multiplayer
-- Server hooks: the authority searches the layout around client 1, sets the fixtures and the moveables down
-- (placeMoveable on the server, what ISMoveablesAction:complete runs there), then asks client 1 by test messages
-- (module LWTTest) to act; client 1 acts only through the real commands (sendClientCommand, module LiveWater:
-- lay, switchValve, fitFilter), teleported by /teleportto. The authority checks its state after real
-- EveryTenMinutes steps; client 1 checks what reached it (pipe sprites, inlet sprite).

local TEST = "LWTTest"

local function layoutArgs(L)
    local pipes = {}
    for i = 1, #L.pipes do pipes[i] = { x = L.pipes[i].x, y = L.pipes[i].y } end
    return { pump = L.pump, inlet = L.inlet, sprinkler = L.sprinkler, crop = L.crop, valve = L.valve, pipes = pipes,
        count = #L.pipes }
end

local function tableList(t, n)
    local out = {}
    for i = 1, n do out[i] = t[i] end
    return out
end

local M = {}

local function mpPlayer()
    return M.player
end

local function tell(command, args)
    sendServerCommand(mpPlayer(), TEST, command, args or {})
end

local function onTestFromClient(module, command, player, args)
    if module ~= TEST then return end
    M.inbox[#M.inbox + 1] = { command = command, args = args or {} }
end

local function received(command)
    for i = 1, #M.inbox do
        if M.inbox[i].command == command and not M.inbox[i].used then
            M.inbox[i].used = true
            return M.inbox[i].args
        end
    end
    return nil
end

local function serverWait(n)
    return function()
        if not M.waitFrom then
            M.waitFrom = S.tens or 0
            resetSeen()
        end
        if (S.tens or 0) - M.waitFrom >= n then
            M.waitFrom = nil
            return true
        end
        return false
    end
end

local function serverSteps(ctx)
    local P = ctx.params or {}
    local radius = tonumber(P.radius) or 40
    local stepSec = tonumber(P.stepSec) or 90

    addStep("client 1 connected and arrived", function()
        local list = ctx.players and ctx.players() or {}
        M.player = list[1]
        if not M.player then return false end
        local a = received("arrived")
        if not a then return false end
        M.center = { x = a.x, y = a.y }
        M.arrivedAt = nowMs()
        return true
    end, 240)

    addStep("layout found near water (server)", function()
        if nowMs() - M.arrivedAt < 8000 then return false end
        if M.retry then
            local a = received("arrived")
            if not a then return false end
            M.center, M.retry, M.arrivedAt = { x = a.x, y = a.y }, nil, nowMs()
            return false
        end
        local L, why = findLayout(M.center.x, M.center.y, radius)
        if not L then
            info("no layout around " .. key(M.center.x, M.center.y) .. ": " .. tostring(why))
            M.retry = true
            tell("next")
            return false
        end
        S.L = L
        rec(true, "layout found near water (server)", describe(L))
        return true
    end, 300)

    addStep("fixtures and moveables set down on the server", function()
        local L, pl = S.L, mpPlayer()
        pl:setGodMod(true)
        pl:setInvisible(true)
        giveItems(pl, { { "LiveWater.PipeSection", 80 }, { "LiveWater.WaterFilter", 1 }, { "Base.PipeWrench", 1 },
            { "Base.Mov_LiveWater_PondPump", 1 }, { "Base.Mov_LiveWater_HouseInlet", 1 },
            { "Base.Mov_LiveWater_Sprinkler", 1 }, { "Base.Mov_LiveWater_Valve", 1 } })
        S.gen = makeGenerator(L.gen)
        local plantObj = plant(L.crop)
        plumb(L.fixture.obj)
        rec(S.gen:isActivated() and plantObj ~= nil and L.fixture.obj:getUsesExternalWaterSource(),
            "generator on, crop seeded, fixture plumbed")
        local ok1, w1 = placeMoveable(pl, PUMP_SPRITE, L.pump)
        local ok2, w2 = placeMoveable(pl, INLET_SPRITE, L.inlet)
        local ok3, w3 = placeMoveable(pl, SPRINKLER_SPRITE, L.sprinkler)
        local e1, e2, e3 = entryAt(L.pump), entryAt(L.inlet), entryAt(L.sprinkler)
        rec(ok1 and e1 ~= nil and e1.data.intake and e1.data.intake.source == "water",
            "pond pump set down next to water (server placement)", tostring(w1 or "") .. " "
            .. tostring(e1 and e1.data.intake and e1.data.intake.source))
        rec(ok2 and ok3 and e2 ~= nil and e3 ~= nil, "house inlet and sprinkler set down (server placement)",
            tostring(w2 or "") .. " " .. tostring(w3 or ""))
        tell("lay", layoutArgs(L))
        return true
    end)

    addStep("pipes laid by client 1 (lay commands)", function()
        for i = 1, #S.L.pipes do
            if not entryAt(S.L.pipes[i]) then return false end
        end
        rec(true, "pipes laid by client 1 (lay commands)", #S.L.pipes .. " pipes")
        local ok, why = placeMoveable(mpPlayer(), VALVE_SPRITE, S.L.valve)
        local e = entryAt(S.L.valve)
        rec(ok and e ~= nil and e.type == VALVE, "inline valve set down between two pipes (server placement)",
            tostring(why or ""))
        return true
    end, 300)

    addStep("network built with sprites by side mask (server)", function()
        local L, s = S.L, server()
        local id = s.network:networkAt(L.pump.x, L.pump.y, 0)
        local apart, all = 0, { L.inlet, L.sprinkler, L.valve }
        for i = 1, #L.pipes do all[#all + 1] = L.pipes[i] end
        for i = 1, #all do
            if s.network:networkAt(all[i].x, all[i].y, 0) ~= id then apart = apart + 1 end
        end
        rec(id ~= nil and apart == 0, "one network (server)", "parts outside " .. apart)
        local wrong = 0
        for i = 1, #L.pipes do
            if spriteOf(L.pipes[i], PIPE) ~= SHEET .. expectedMask(L, L.pipes[i]) then wrong = wrong + 1 end
        end
        rec(wrong == 0, "pipe sprites by side mask (server)", "wrong " .. wrong)
        tell("open")
        return true
    end)

    addStep("sprinkler valve opened by client 1", function()
        local e = entryAt(S.L.sprinkler)
        if not (e and e.data.valve and e.data.valve.open == true) then return false end
        local pl = plantAt(S.L.crop)
        S.levelBefore = pl and pl.waterLvl or -1
        rec(true, "sprinkler valve opened by client 1 (switchValve)")
        return true
    end, 60)

    addStep("two ten-minute steps without filter", serverWait(2), stepSec * 2)

    addStep("checks without filter (server)", function()
        local L = S.L
        local seen = S.seen
        info(seenText())
        rec(seen.powered and seen.running, "pump powered and running (server)")
        local n, amount = relaysOf(L)
        rec(seen.inlet.unfiltered and not seen.inlet.served and amount <= 0.001,
            "house inlet refuses unfiltered water (server)", "litres " .. amount)
        local pl = plantAt(L.crop)
        rec(seen.sprinkler.served and pl and pl.waterLvl > S.levelBefore, "sprinkler waters the crop (server)",
            "level " .. tostring(S.levelBefore) .. " -> " .. tostring(pl and pl.waterLvl))
        tell("filter")
        return true
    end)

    addStep("filter fitted by client 1", function()
        local f = entryAt(S.L.pump).data.filter
        if not (f and f.fitted == true) then return false end
        rec(true, "filter fitted by client 1 (fitFilter)")
        return true
    end, 60)

    addStep("two ten-minute steps with filter", serverWait(2), stepSec * 2)

    addStep("checks with filter (server)", function()
        local L = S.L
        info(seenText())
        local n, amount = relaysOf(L)
        rec(S.seen.inlet.served and amount > 0, "house inlet served, relay filled (server)",
            "relays " .. n .. " litres " .. amount)
        local obj = L.fixture.obj
        local clean, tainted = relayFluids(L)
        rec(obj:getFluidAmount() > 0 and clean > 0 and tainted <= 0.001, "the plumbed fixture gives clean water (server)",
            "fixture litres " .. tostring(obj:getFluidAmount()) .. ", tank clean " .. clean .. " tainted " .. tainted)
        tell("inline")
        return true
    end)

    addStep("inline valve closed by client 1", function()
        local e = entryAt(S.L.valve)
        if not (e and e.data.valve and e.data.valve.open == false) then return false end
        drainRelays(S.L)
        local pl = plantAt(S.L.crop)
        pl.waterLvl = 0
        pl:saveData()
        rec(true, "inline valve closed by client 1 (switchValve)", "relays emptied, crop dry (fixture)")
        return true
    end, 60)

    addStep("two ten-minute steps with the inline valve closed", serverWait(2), stepSec * 2)

    addStep("checks with the inline valve closed (server)", function()
        local L, seen = S.L, S.seen
        info(seenText())
        local n, amount = relaysOf(L)
        rec(not seen.inlet.served and amount <= 0.001, "closed inline valve stops the house inlet (server)",
            "litres " .. amount)
        local pl = plantAt(L.crop)
        rec(seen.sprinkler.served and pl and pl.waterLvl > 0, "the sprinkler upstream still waters (server)",
            "level " .. tostring(pl and pl.waterLvl))
        tell("close")
        return true
    end)

    addStep("sprinkler valve closed by client 1", function()
        local e = entryAt(S.L.sprinkler)
        if not (e and e.data.valve and e.data.valve.open == false) then return false end
        local pl = plantAt(S.L.crop)
        pl.waterLvl = 0
        pl:saveData()
        rec(true, "sprinkler valve closed by client 1 (switchValve)")
        return true
    end, 60)

    addStep("two ten-minute steps with the valve closed", serverWait(2), stepSec * 2)

    addStep("checks with the valve closed (server)", function()
        local L = S.L
        local sstate = entryAt(L.sprinkler).data.outlet and entryAt(L.sprinkler).data.outlet.state
        local pl = plantAt(L.crop)
        info(seenText())
        rec(sstate == "closed" and not S.seen.sprinkler.served and pl and pl.waterLvl <= 0,
            "closed valve stops the branch (server)",
            "state " .. tostring(sstate) .. " level " .. tostring(pl and pl.waterLvl))
        tell("end")
        M.endAt = nowMs()
        return true
    end)

    addStep("client 1 told the end", function()
        return nowMs() - M.endAt > 5000
    end, 20)
end

function H.server.start(ctx)
    R = { lines = {}, ok = true, steps = {}, index = 0 }
    S, M = {}, { inbox = {} }
    Events.OnClientCommand.Add(onTestFromClient)
    Events.EveryTenMinutes.Add(onTen)
    serverSteps(ctx)
    return true
end

function H.server.done(ctx)
    clearZombies()
    local finished = runSteps()
    if finished then
        Events.EveryTenMinutes.Remove(onTen)
        Events.OnClientCommand.Remove(onTestFromClient)
    end
    return finished
end

function H.server.result(ctx)
    return summary()
end

-- Client 1 (mp): acts on the test messages of the server.
local C = {}

local function cplayer()
    return getPlayer()
end

local function cnear(p, d)
    local pl = cplayer()
    return math.abs(math.floor(pl:getX()) - p.x) <= d and math.abs(math.floor(pl:getY()) - p.y) <= d
end

local function teleportClient(p)
    SendCommandToServer("/teleportto " .. p.x .. "," .. p.y .. ",0")
end

local function onTestFromServer(module, command, args)
    if module ~= TEST then return end
    C.queue[#C.queue + 1] = { command = command, args = args or {} }
end

-- Bring the player near p, then run fn once (after a short settle so that the server has the position).
local function actNear(p, fn)
    if not cnear(p, 2) then
        if not C.tpAt or nowMs() - C.tpAt > 5000 then
            teleportClient(p)
            C.tpAt = nowMs()
        end
        C.nearAt = nil
        return false
    end
    C.nearAt = C.nearAt or nowMs()
    if nowMs() - C.nearAt < 1500 then return false end
    fn()
    C.tpAt, C.nearAt = nil, nil
    return true
end

local function clientArrive(centers)
    C.centerIndex = C.centerIndex + 1
    C.center = centers[C.centerIndex]
    C.arrivedSent = false
    if C.center then teleportClient(C.center) end
end

local function clientSpriteOf(p, typeId)
    return spriteOf(p, typeId)
end

local function clientChecks()
    local L = C.L
    local wrong = 0
    for i = 1, #L.pipes do
        if clientSpriteOf(L.pipes[i], PIPE) ~= SHEET .. expectedMask(L, L.pipes[i]) then wrong = wrong + 1 end
    end
    rec(wrong == 0, "client 1 sees the pipe sprites by side mask", #L.pipes .. " pipes, wrong " .. wrong)
    local isprite = clientSpriteOf(L.inlet, "LiveWater:HouseInlet")
    rec(isprite == SHEET .. "40", "client 1 sees the house inlet green (filtered)", tostring(isprite))
    local vs = clientSpriteOf(L.valve, VALVE)
    rec(vs == SHEET .. valveIndex(L, false), "client 1 sees the inline valve closed", tostring(vs))
    local ssprite = clientSpriteOf(L.sprinkler, "LiveWater:Sprinkler")
    rec(ssprite ~= nil, "client 1 sees the sprinkler", tostring(ssprite))
    local n = getLuaDebuggerErrorCount and getLuaDebuggerErrorCount() or 0
    rec(n == 0, "no Lua error recorded (client 1)", "errors=" .. tostring(n))
end

local function clientDone(ctx)
    clearZombies()
    if C.finished then return true end
    local pl = cplayer()
    pl:setGodMod(true)
    pl:setInvisible(true)
    if C.center and not C.arrivedSent and cnear(C.center, 3) then
        C.arrivedAt = C.arrivedAt or nowMs()
        if nowMs() - C.arrivedAt > 3000 then
            sendClientCommand(pl, TEST, "arrived", { x = C.center.x, y = C.center.y })
            C.arrivedSent, C.arrivedAt = true, nil
        end
    elseif C.center and not C.arrivedSent and (not C.tpAt or nowMs() - C.tpAt > 8000) then
        teleportClient(C.center)
        C.tpAt = nowMs()
    end
    if C.action then
        if C.action() then C.action = nil end
        return false
    end
    local msg = table.remove(C.queue, 1)
    if not msg then
        if nowMs() - C.startedAt > C.limitMs then
            rec(false, "client 1 finished before its deadline")
            return true
        end
        return false
    end
    local a = msg.args
    if msg.command == "next" then
        clientArrive(C.centers)
        if not C.center then
            rec(false, "client 1 layout place", "no candidate place left")
            return true
        end
    elseif msg.command == "lay" then
        C.L = { pump = a.pump, inlet = a.inlet, sprinkler = a.sprinkler, crop = a.crop, valve = a.valve,
            pipes = tableList(a.pipes, a.count) }
        C.pi = 0
        C.action = function()
            if C.current then
                if clientSpriteOf(C.current, PIPE) or nowMs() - C.sentAt > 10000 then C.current = nil end
                return false
            end
            local p = C.L.pipes[C.pi + 1]
            if not p then
                rec(true, "client 1 sent the lay commands", #C.L.pipes .. " pipes")
                return true
            end
            actNear(p, function()
                C.pi = C.pi + 1
                sendClientCommand(cplayer(), MODULE, "lay", { x = p.x, y = p.y, z = 0, part = PIPE })
                C.current, C.sentAt = p, nowMs()
            end)
            return false
        end
    elseif msg.command == "inline" then
        local v = C.L.valve
        C.action = function()
            return actNear(v, function() sendClientCommand(cplayer(), MODULE, "switchValve", { x = v.x, y = v.y, z = 0 }) end)
        end
    elseif msg.command == "open" or msg.command == "close" then
        local s = C.L.sprinkler
        C.action = function()
            return actNear(s, function() sendClientCommand(cplayer(), MODULE, "switchValve", { x = s.x, y = s.y, z = 0 }) end)
        end
    elseif msg.command == "filter" then
        local p = C.L.pump
        C.action = function()
            return actNear(p, function() sendClientCommand(cplayer(), MODULE, "fitFilter", { x = p.x, y = p.y, z = 0 }) end)
        end
    elseif msg.command == "end" then
        clientChecks()
        C.finished = true
        return true
    end
    return false
end

function H.client.start(ctx)
    R = { lines = {}, ok = true, steps = {}, index = 0 }
    S = {}
    if ctx.ready and not ctx.ready.ok then info("world barrier: " .. tostring(ctx.ready.detail)) end
    if isClient() then
        C = { queue = {}, centers = centersOf(ctx.params and ctx.params.centers), centerIndex = 0,
            startedAt = nowMs(), limitMs = (tonumber(ctx.params and ctx.params.clientWaitSec) or 1500) * 1000 }
        Events.OnServerCommand.Add(onTestFromServer)
        clientArrive(C.centers)
        return true
    end
    buildSteps(ctx)
    return true
end

function H.client.done(ctx)
    if isClient() then
        local finished = clientDone(ctx)
        if finished then Events.OnServerCommand.Remove(onTestFromServer) end
        return finished
    end
    clearZombies()
    keepDry()
    local finished = runSteps()
    if finished then
        Events.EveryTenMinutes.Remove(onTen)
        setGameSpeed(1)
    end
    return finished
end

function H.client.result(ctx)
    return summary()
end

return H
