-- LiveWater: the state of a part mirrored on its game object (ADR-001 D11), both sides. The
-- authority writes it (LWT_Publisher through LWT_GameWorld) and sends it to the clients; menus
-- and Live Wire read it. It lives in the object's movableData, which the vanilla furniture
-- pickup copies into the item and the placement copies back (ISMoveableSpriteProps), so a pump
-- carried elsewhere keeps its wear and its filter.
--   ModData.movableData.LiveWater = { type = part type id, data = { [kind] = state } }

local Mirror = {}

Mirror.KEY = "LiveWater"

local function copy(v)
    if type(v) ~= "table" then return v end
    local out = {}
    for k, x in pairs(v) do out[k] = copy(x) end
    return out
end

-- { type, data } mirrored on the object, or nil.
function Mirror.read(obj)
    local md = obj and obj:getModData()
    local movable = md and md.movableData
    local state = type(movable) == "table" and movable[Mirror.KEY]
    if type(state) ~= "table" or type(state.type) ~= "string" then return nil end
    return state
end

-- Write a copy of { type, data } on the object (the caller sends it to the clients).
function Mirror.write(obj, state)
    local md = obj:getModData()
    if type(md.movableData) ~= "table" then md.movableData = {} end
    md.movableData[Mirror.KEY] = copy(state)
end

return Mirror
