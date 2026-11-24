-- LiveWater: the pipe wrench rule of the plumbing actions, both sides (ADR-024 D01, D04). The game
-- itself accepts a pipe wrench by type or by tag, in the inventory (bags included), as long as it is
-- not broken (Java 42.22 ISWorldObjectContextMenuLogic.doWaterPipeMenu; ISWorldObjectContextMenu
-- .onPlumbItem rescans and equips it; ISPlumbItem:isValid requires it equipped). The client options
-- of LiveWater and the authority's command ask this one module, so an option is never offered and
-- then refused as "need_tool".
--   TYPE                 type of the game's pipe wrench
--   tag()                the game's pipe wrench tag (ItemTag.PIPE_WRENCH)
--   first(inventory)     first usable pipe wrench of an ItemContainer (bags included), or nil
--   brokenFirst(inventory)  first broken pipe wrench of an ItemContainer, or nil
--   of(player)           first usable pipe wrench in the player's inventory, or nil
--   problem(player)      nil when the player may plumb with a pipe wrench; "wrench_broken" when
--                        he carries pipe wrenches but all of them are broken; "no_wrench" when he
--                        carries none. nil without a player (nothing to say).

local Wrench = {}

Wrench.TYPE = "PipeWrench"

-- The tag of the game's pipe wrench (ItemTag.PIPE_WRENCH, item script tags "base:pipewrench").
function Wrench.tag()
    return ItemTag.PIPE_WRENCH
end

local function notBroken(item) return not item:isBroken() end
local function broken(item) return item:isBroken() end

function Wrench.first(inventory)
    if not inventory then return nil end
    return inventory:getFirstTypeEvalRecurse(Wrench.TYPE, notBroken)
        or inventory:getFirstTagEvalRecurse(Wrench.tag(), notBroken)
end

function Wrench.brokenFirst(inventory)
    if not inventory then return nil end
    return inventory:getFirstTypeEvalRecurse(Wrench.TYPE, broken)
        or inventory:getFirstTagEvalRecurse(Wrench.tag(), broken)
end

function Wrench.of(player)
    if not player then return nil end
    return Wrench.first(player:getInventory())
end

function Wrench.problem(player)
    local inventory = player and player:getInventory()
    if not inventory then return nil end
    if Wrench.first(inventory) then return nil end
    if Wrench.brokenFirst(inventory) then return "wrench_broken" end
    return "no_wrench"
end

return Wrench
