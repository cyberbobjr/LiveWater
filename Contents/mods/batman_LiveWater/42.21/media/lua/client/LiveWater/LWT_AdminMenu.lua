-- LiveWater: admin right-click option "Remove LiveWater from this world" (ADR-001 P21, L14; ADR-016).
-- Offered to an admin in multiplayer and, in solo, only in debug mode (LWT_RemovalRight); a dialog asks
-- for a confirmation, then the command removeLiveWater goes to the authority, which checks the same
-- right again (LWT_CmdRemoveAll, LWT_Removal). Then save and unsubscribe: the save stays readable.

local Protocol = require "LiveWater/LWT_Protocol"
local RemovalRight = require "LiveWater/LWT_RemovalRight"

local AdminMenu = {}

AdminMenu.allowed = RemovalRight.allowed

local function onConfirm(_, button, player)
    if button.internal == "YES" then sendClientCommand(player, Protocol.MODULE, Protocol.REMOVE_ALL, {}) end
end

local function confirm(player)
    local modal = ISModalDialog:new(0, 0, 360, 160, getText("IGUI_LWT_RemoveConfirm"), true, nil, onConfirm, player)
    modal:initialise()
    modal:addToUIManager()
end

function AdminMenu.fill(playerNum, context, worldobjects, test)
    local player = getSpecificPlayer(playerNum)
    if not player or test or not AdminMenu.allowed(player) then return end
    context:addOption(getText("ContextMenu_LWT_RemoveMod"), player, confirm)
end

Events.OnFillWorldObjectContextMenu.Add(AdminMenu.fill)

return AdminMenu
