-- LiveWater: debug-only right-click submenu "LiveWater (debug)" > "Give the Test Kit". Shown only when
-- the game runs with -debug. The kit is every item of the mod (module LiveWater and the moveables
-- Base.Mov_LiveWater_*, read from the scripts: a new part joins the kit by itself), with 20 pipe
-- sections and 20 drip lines, and the pipe wrench that dismantles parts. Solo: added to the inventory; on a server:
-- the /additem command, which the server allows to admins only.

local DebugMenu = {}

DebugMenu.COUNTS = { ["Base.Mov_LiveWater_Pipe"] = 20, ["Base.Mov_LiveWater_DripLine"] = 20 }
DebugMenu.EXTRA = { "Base.PipeWrench" }

local function ours(name)
    return name:sub(1, 10) == "LiveWater." or name:sub(1, 19) == "Base.Mov_LiveWater_"
end

-- Full names of the kit, sorted, mod items first then the extra tools.
function DebugMenu.kit()
    local names, all = {}, getAllItems()
    for i = 0, all:size() - 1 do
        local name = all:get(i):getFullName()
        if ours(name) then names[#names + 1] = name end
    end
    table.sort(names)
    for i = 1, #DebugMenu.EXTRA do names[#names + 1] = DebugMenu.EXTRA[i] end
    return names
end

local function give(player)
    local names = DebugMenu.kit()
    for i = 1, #names do
        local name, count = names[i], DebugMenu.COUNTS[names[i]] or 1
        if isClient() then
            SendCommandToServer('/additem "' .. player:getUsername() .. '" "' .. name .. '" ' .. count)
        else
            for _ = 1, count do player:getInventory():AddItem(name) end
        end
    end
end

function DebugMenu.fill(playerNum, context, worldobjects, test)
    if test or not isDebugEnabled() then return end
    local player = getSpecificPlayer(playerNum)
    if not player then return end
    local root = context:addOption(getText("ContextMenu_LWT_Debug"))
    local sub = ISContextMenu:getNew(context)
    context:addSubMenu(root, sub)
    sub:addOption(getText("ContextMenu_LWT_DebugKit"), player, give)
end

Events.OnFillWorldObjectContextMenu.Add(DebugMenu.fill)

return DebugMenu
