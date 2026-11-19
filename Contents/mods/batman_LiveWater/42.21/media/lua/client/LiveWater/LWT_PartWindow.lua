-- LiveWater: window of a part opened from "Information", client (ADR-008 D03, D07). It shows the
-- part through a face (LWT_Panels: the water meter's rolling digits, the pump's LCD) and keeps up
-- with it while open: every REFRESH_MS it reads again the state mirrored on the object (LWT_Mirror,
-- sent by the authority after each step) and grows to fit longer lines. Nothing is computed per
-- frame but a clock comparison; no event is subscribed. It closes when the part leaves its square
-- or the player walks farther than RANGE squares. One window at a time.

require "ISUI/ISCollapsableWindow"
require "LiveWater/LWT_API"
local Mirror = require "LiveWater/LWT_Mirror"
local PartText = require "LiveWater/LWT_PartText"
local Panels = require "LiveWater/LWT_Panels"

local PartWindow = ISCollapsableWindow:derive("LWT_PartWindow")

PartWindow.REFRESH_MS = 1000
PartWindow.RANGE = 4
PartWindow.PAD = 10
PartWindow.instance = nil

-- What the window shows of the part of type `typeId` mirrored on `obj`: { title, reading, lines,
-- keys (translation key of each line) }.
function PartWindow.view(obj, typeId, catalog)
    local state = Mirror.read(obj)
    local part = { type = typeId, data = state and state.type == typeId and state.data or {} }
    local _, title, reading = catalog:first(part, "panel")
    local lines, keys = PartText.texts(catalog, part)
    return { title = title, reading = reading, lines = lines, keys = keys }
end

local function near(player, obj)
    local sq = obj and obj:getSquare()
    if not sq or not player then return false end
    local dx, dy = player:getX() - sq:getX(), player:getY() - sq:getY()
    return math.floor(player:getZ()) == sq:getZ() and dx * dx + dy * dy <= PartWindow.RANGE * PartWindow.RANGE
end

-- Outer size a face needs to show a view.
local function wanted(face, view)
    local w, h = face.size(view)
    return w + 2 * PartWindow.PAD, h + 2 * PartWindow.PAD + ISCollapsableWindow.TitleBarHeight()
end

function PartWindow.open(player, obj, typeId, face)
    if PartWindow.instance then PartWindow.instance:close() end
    local num = player:getPlayerNum()
    local view = PartWindow.view(obj, typeId, LiveWater.Parts)
    local w, h = wanted(face, view)
    local win = PartWindow:new(getPlayerScreenLeft(num) + 120, getPlayerScreenTop(num) + 90, w, h)
    win.player, win.obj, win.typeId, win.face, win.view = player, obj, typeId, face, view
    win.lastRead = getTimestampMs()
    win:setTitle(getText(view.title or "ContextMenu_LWT_Info"))
    win:setResizable(false)
    win:initialise()
    win:addToUIManager()
    PartWindow.instance = win
    return win
end

-- Read the part again; close when it is gone or out of reach.
function PartWindow:refresh()
    if not near(self.player, self.obj) then
        self:close()
        return
    end
    self.view = PartWindow.view(self.obj, self.typeId, LiveWater.Parts)
    local w, h = wanted(self.face, self.view)
    if w > self.width then self:setWidth(w) end
    if h > self.height then self:setHeight(h) end
end

function PartWindow:update()
    ISCollapsableWindow.update(self)
    if self.closed then return end
    local now = getTimestampMs()
    if now - self.lastRead >= PartWindow.REFRESH_MS then
        self.lastRead = now
        self:refresh()
    end
end

function PartWindow:render()
    ISCollapsableWindow.render(self)
    if self.closed or self.isCollapsed then return end
    self.face.draw(self, self.view, PartWindow.PAD, self:titleBarHeight() + PartWindow.PAD)
end

function PartWindow:close()
    if self.closed then return end
    self.closed = true
    self:setVisible(false)
    self:removeFromUIManager()
    if PartWindow.instance == self then PartWindow.instance = nil end
end

Panels.window = PartWindow.open

return PartWindow
