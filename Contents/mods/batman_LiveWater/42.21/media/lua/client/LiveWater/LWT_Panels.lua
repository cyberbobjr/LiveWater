-- LiveWater: registry of the window faces of "Information", client (ADR-008 D03, D07). A part's
-- capability names the face of its window (`panel` hook: "counter" for the water meter, "lcd" for
-- the pump); a face is a strategy table registered here by its own file:
--   size(view)              width and height of what it draws, in pixels
--   draw(ui, view, x, y)    draws the view at x, y of the window ui
-- view = { title, reading, lines, keys } (LWT_PartWindow.view). The window that holds a face is a port:
--   Panels.window(player, obj, typeId, face)  set by LWT_PartWindow when it loads
-- A part whose face is not registered (or without a window) keeps the tooltip (LWT_PartMenu).

local Panels = { faces = {}, window = nil }

-- Returns true, or false when the name is taken or the face is not a table.
function Panels.register(name, face)
    if type(name) ~= "string" or type(face) ~= "table" or Panels.faces[name] then return false end
    Panels.faces[name] = face
    return true
end

-- The face registered under `name`, when a window can hold it; else nil.
function Panels.get(name)
    if not name or not Panels.window then return nil end
    return Panels.faces[name]
end

-- Open the window of a part ({ type, data, object }) with the face `name` (context menu target).
function Panels.open(player, name, part)
    local face = Panels.get(name)
    if face then Panels.window(player, part.object, part.type, face) end
end

return Panels
