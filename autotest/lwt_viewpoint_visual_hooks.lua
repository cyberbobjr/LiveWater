-- Viewpoint visual check: places LiveWater parts next to the player (direct object creation, not the
-- build menu), then cycles Viewpoint's views and takes one screenshot per view. The screenshots must be
-- opened and inspected: this hook proves nothing about the picture by itself.
local H = {}
local SHEET = "batman_livewater_01_"
local lines = {}
local began, step, stepAt
local okay = true

local function note(text) lines[#lines + 1] = text end

local function clearZombies()
    local zombies = getCell():getZombieList()
    for i = zombies:size() - 1, 0, -1 do
        local z = zombies:get(i)
        z:removeFromWorld()
        z:removeFromSquare()
    end
end

local function place(player, dx, dy, index)
    local sq = getCell():getGridSquare(player:getX() + dx, player:getY() + dy, player:getZ())
    if not sq then
        note("FAIL no square at offset " .. dx .. "," .. dy)
        okay = false
        return nil
    end
    local obj = IsoObject.new(getCell(), sq, SHEET .. tostring(index))
    sq:AddTileObject(obj)
    note("INFO placed " .. SHEET .. tostring(index) .. " at " .. sq:getX() .. "," .. sq:getY())
    return obj
end

function H.start()
    began = getTimestampMs()
    step, stepAt = 0, began
    local player = getSpecificPlayer(0)
    player:setGodMod(true)
    player:setInvisible(true)
    clearZombies()
    getGameTime():setTimeOfDay(12.0)
    -- Water pump straight ahead, house inlet and sprinkler beside it.
    local solar = place(player, 2, 0, 24)
    place(player, 2, 1, 40)
    place(player, 2, -1, 48)
    if solar then player:faceThisObject(solar) end
    note("INFO Viewpoint.View exposed: " .. tostring(Viewpoint ~= nil and Viewpoint.View ~= nil))
    return true
end

function H.done()
    clearZombies()
    local now = getTimestampMs()
    -- Viewpoint first builds its world ("Preparing first person", up to a minute): wait before the first shot.
    local wait = step == 0 and 100000 or 15000
    if now - stepAt < wait then return false end
    stepAt = now
    step = step + 1
    if step <= 3 then
        takeScreenshot("vp-view" .. tostring(step) .. ".png")
        note("INFO screenshot vp-view" .. tostring(step) .. ".png, next view would be: "
            .. tostring(Viewpoint and Viewpoint.View and Viewpoint.View.next()))
        return false
    end
    return true
end

function H.result()
    return { ok = okay, summary = "3 views captured; screenshot inspection required", lines = lines }
end

return H
