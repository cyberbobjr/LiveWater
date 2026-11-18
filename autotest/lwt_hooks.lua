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

-- Free for a part (the rule of LWT_GameWorld:isFree), outdoors, nothing else standing there.
local function free(s)
    if not s or not s:getFloor() then return false end
    if s:has(IsoFlagType.water) or s:isSolid() or s:isSolidTrans() or s:HasTree() then return false end
    if not s:isOutside() or s:getBuilding() ~= nil then return false end
    local objects = s:getObjects()
    for i = 0, objects:size() - 1 do
        local obj = objects:get(i)
        local name = obj:getSpriteName() or ""
        if obj ~= s:getFloor() and not (string.find(name, "^e_") or string.find(name, "^blends_")
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

-- A free outdoor square orthogonally next to the building of `f`, within 15 squares of the fixture.
local function inletTargets(fixtures, cx, cy, r)
    local targets = {}
    for i = 1, #fixtures do
        local f = fixtures[i]
        for x = f.x - 15, f.x + 15 do
            for y = f.y - 15, f.y + 15 do
                local dx, dy = x - f.x, y - f.y
                if dx * dx + dy * dy <= 225 and math.abs(x - cx) <= r and math.abs(y - cy) <= r then
                    local s = sq(x, y, 0)
                    if free(s) and not nearWater(x, y) then
                        for j = 1, 4 do
                            local n = sq(x + SIDES[j][1], y + SIDES[j][2], 0)
                            if n and mapBuilding(n) == f.def and not targets[key(x, y)] then
                                targets[key(x, y)] = { x = x, y = y, fixture = f }
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

-- Breadth-first search from every pump square to the nearest inlet square through free squares.
local function findLayout(cx, cy, r)
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
    local targets = inletTargets(fixtures, cx, cy, r)
    local queue, prev, head = {}, {}, 1
    for x = cx - r, cx + r do
        for y = cy - r, cy + r do
            if free(sq(x, y, 0)) and nearWater(x, y) then
                queue[#queue + 1] = { x = x, y = y }
                prev[key(x, y)] = "start"
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
        for j = 1, 4 do
            local x, y = n.x + SIDES[j][1], n.y + SIDES[j][2]
            local k = key(x, y)
            if not prev[k] and math.abs(x - cx) <= r and math.abs(y - cy) <= r and free(sq(x, y, 0)) then
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
    local L = { pump = chain[1], inlet = chain[#chain], fixture = targets[key(goal.x, goal.y)].fixture, pipes = {} }
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
        .. " valve " .. key(L.valve.x, L.valve.y)
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

-- Vanilla moveable placement (ISMoveablesAction:complete -> ISMoveableSpriteProps:placeMoveable).
local function placeMoveable(player, spriteName, p)
    local props = ISMoveableSpriteProps.new(getSprite(spriteName))
    local square = sq(p.x, p.y, 0)
    local item = props:findInInventory(player, spriteName)
    if not item then return false, "moveable item not in inventory" end
    if not props:canPlaceMoveableInternal(player, square, item) then return false, "canPlaceMoveable refused" end
    props:placeMoveable(player, square, spriteName)
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

local function near(p, q, d)
    return math.abs(p.x - q.x) <= d and math.abs(p.y - q.y) <= d
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

local function buildSteps(ctx)
    local P = ctx.params or {}
    local radius = tonumber(P.radius) or 40
    local stepSec = tonumber(P.stepSec) or 90
    local centers = centersOf(P.centers)
    S.centerIndex = 0

    addStep("player untouchable and items given", function()
        local pl = player()
        pl:setGodMod(true)
        pl:setInvisible(true)
        giveItems(pl, { { "LiveWater.PipeSection", 80 }, { "LiveWater.WaterFilter", 1 }, { "Base.PipeWrench", 1 },
            { "Base.Mov_LiveWater_PondPump", 1 }, { "Base.Mov_LiveWater_HouseInlet", 1 },
            { "Base.Mov_LiveWater_Sprinkler", 1 }, { "Base.Mov_LiveWater_Valve", 1 } })
        rec(server() ~= nil, "LiveWater authority built (LiveWater.Server)")
        Events.EveryTenMinutes.Add(onTen)
        return true
    end)

    addStep("layout found near water", function()
        if not S.center then
            S.centerIndex = S.centerIndex + 1
            S.center = centers[S.centerIndex]
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
        local L, why = findLayout(c.x, c.y, radius)
        if not L then
            info("no layout around " .. key(c.x, c.y) .. ": " .. tostring(why))
            S.center = nil
            return false
        end
        S.L = L
        rec(true, "layout found near water", "around " .. key(c.x, c.y) .. ": " .. describe(L))
        return true
    end, 300)

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
        local ok, why = placeMoveable(player(), PUMP_SPRITE, S.L.pump)
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
        local ok1, why1 = placeMoveable(player(), INLET_SPRITE, L.inlet)
        goNear(L.sprinkler)
        local ok2, why2 = placeMoveable(player(), SPRINKLER_SPRITE, L.sprinkler)
        goNear(L.valve)
        local ok3, why3 = placeMoveable(player(), VALVE_SPRITE, L.valve)
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
        local all = { L.inlet, L.sprinkler, L.valve }
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
        rec(seen.powered and seen.running and seen.pumpSprite[SHEET .. "28"] == true,
            "pump powered by the generator, running, sprite on")
        if P.livewire == "1" then
            rec(seen.consumer == true and (seen.watts or 0) > 0, "Live Wire knows the pump as a consumer and bills it",
                "watts " .. tostring(seen.watts))
        end
        local n, amount = relaysOf(L)
        local isprite = spriteOf(L.inlet, "LiveWater:HouseInlet")
        rec(seen.inlet.unfiltered and not seen.inlet.served and amount <= 0.001,
            "house inlet refuses unfiltered pond water", "relays " .. n .. " litres " .. amount)
        rec(isprite == SHEET .. "44", "house inlet sprite amber (unfiltered)", tostring(isprite))
        local pl = plantAt(L.crop)
        local level = pl and pl.waterLvl or -1
        rec(seen.sprinkler.served and level > S.levelBefore, "sprinkler waters the crop",
            "water level " .. tostring(S.levelBefore) .. " -> " .. tostring(level))
        return true
    end)

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
        rec(isprite == SHEET .. "40", "house inlet sprite green (filtered)", tostring(isprite))
        local obj = L.fixture.obj
        rec(obj:getFluidAmount() > 0 and obj:hasWater() and not obj:isTaintedWater(),
            "the plumbed fixture gives clean water", "litres " .. tostring(obj:getFluidAmount()) .. " tainted "
            .. tostring(obj:isTaintedWater()))
        rec(seen.pumpSprite[SHEET .. "32"] == true, "pump sprite running with filter")
        return true
    end)

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
        rec(obj:getFluidAmount() > 0 and not obj:isTaintedWater(), "the plumbed fixture gives clean water (server)",
            "litres " .. tostring(obj:getFluidAmount()))
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
