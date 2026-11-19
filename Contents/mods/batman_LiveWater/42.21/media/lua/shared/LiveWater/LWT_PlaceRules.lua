-- LiveWater: placement rules of the parts set down with the vanilla furniture cursor (a pond
-- pump must stand next to a water source, ADR-001 D16, or against a barrel, ADR-011 D01; one part per square, D14: the line of the
-- cursor says so, E13; what only the network knows, such as full ports, is told by the authority
-- when the part is set down, LWT_Placement). A tile is ours when its sprite belongs
-- to a part type; the part's capabilities decide through Parts:attach on the place (LWT_GameSite).
-- Shared: the cursor asks on the client, the authority again when the place action completes
-- (ISMoveablesAction:complete -> placeMoveable -> canPlaceMoveableInternal, server in MP).
-- Wrappers keep the vanilla arguments and results; they only add a refusal for our tiles.

require "Moveables/ISMoveableSpriteProps"
require "LiveWater/LWT_API"
local GameSite = require "LiveWater/LWT_GameSite"
local Reasons = require "LiveWater/LWT_Reasons"
local GameSettings = require "LiveWater/LWT_GameSettings"

-- Barrels a pump may stand against (ADR-011 D01): the rule of the fittings' containers.
local BARRELS = { registry = LiveWater.Containers, listed = GameSettings.listedContainers }

local Rules = {}

-- Does the square already hold a LiveWater part?
local function holdsPart(square)
    local objects = square:getObjects()
    for i = 0, objects:size() - 1 do
        local name = objects:get(i):getSpriteName()
        if name and LiveWater.Parts:typeOfSprite(name) then return true end
    end
    return false
end

-- true, or false and the translation key of the refusal, for a sprite set down on `square`.
function Rules.check(spriteName, square)
    local partType = spriteName and LiveWater.Parts:typeOfSprite(spriteName)
    if not partType or not square then return true end
    if holdsPart(square) then return false, Reasons.key("occupied") end
    local site = GameSite.new(LiveWater.Sources, square:getX(), square:getY(), square:getZ(), BARRELS)
    local ok, reason = LiveWater.Parts:attach({ type = partType }, site)
    if ok then return true end
    return false, Reasons.key(reason)
end

local MP = ISMoveableSpriteProps

local originalCanPlace = MP.canPlaceMoveableInternal
function MP:canPlaceMoveableInternal(_character, _square, _item, ...)
    local ok = originalCanPlace(self, _character, _square, _item, ...)
    if ok and not Rules.check(self.spriteName, _square) then return false end
    return ok
end

local originalInfo = MP.getInfoPanelDescription
function MP:getInfoPanelDescription(_square, _object, _player, _mode, ...)
    local info = originalInfo(self, _square, _object, _player, _mode, ...)
    if _mode == "place" and type(info) == "table" then
        local ok, key = Rules.check(self.spriteName, _square)
        if not ok then info = MP.addLineToInfoTable(info, getText(key), 255, 60, 60) end
    end
    return info
end

return Rules
