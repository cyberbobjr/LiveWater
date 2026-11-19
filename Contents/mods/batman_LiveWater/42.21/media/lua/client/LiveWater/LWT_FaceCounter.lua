-- LiveWater: window face "counter" (ADR-008 D03): an American water meter seen from above. The
-- brass dial (texture FACE_TEXTURE, drawn DIAL x DIAL) has an empty black window where ROLLS
-- rolling digits show the reading (whole litres since the meter was set down; they turn over past
-- 9 999 999 like a real one); the sweep hand (HAND_TEXTURE, turned about its centre) makes one turn
-- every 10 litres. Under the dial: the total, then the information lines of the part (litres of the
-- last ten minutes, the water's quality; unfiltered water in amber).
-- The window of the rolls and the pivot of the hand are fractions of the dial (ROLLS_BOX, HAND),
-- set to match the images. Without the dial texture the rolls are drawn on a plain dark case;
-- without the hand texture there is no hand.
-- The engine draws a turned texture at its own size (UIElement.DrawTextureAngle, Java 42.22): the
-- hand image must be made at the size the dial is shown (DIAL x DIAL), its pivot at the centre.

local Panels = require "LiveWater/LWT_Panels"

local Counter = {}

Counter.ROLLS = 7
Counter.DIAL = 256
Counter.FACE_TEXTURE = "media/textures/LWT_MeterFace.png"
Counter.HAND_TEXTURE = "media/textures/LWT_MeterHand.png"
-- window of the rolls on the dial: x, y, width, height as fractions of the dial
Counter.ROLLS_BOX = { x = 0.305, y = 0.36, w = 0.386, h = 0.083 }
-- pivot of the hand on the dial, fractions
Counter.HAND = { x = 0.5, y = 0.504 }
-- litres of one turn of the hand
Counter.HAND_LITRES = 10
-- rolls drawn without the dial texture
Counter.PLAIN_ROLLS_H = 36
Counter.LINE_GAP = 3
Counter.CASE = { 0.04, 0.04, 0.05 }
Counter.DIGIT = { 0.08, 0.08, 0.08 }
-- rolls: cream, the last one (single litres) orange with a cream digit, shaded top and bottom
Counter.ROLL = { 0.91, 0.89, 0.82 }
Counter.LAST_ROLL = { 0.94, 0.44, 0.08 }
Counter.LAST_DIGIT = { 1.0, 0.98, 0.94 }
Counter.SHADE = 0.45
Counter.TEXT = { 0.88, 0.88, 0.86 }
Counter.AMBER = { 0.94, 0.44, 0.08 }
-- colour of a line by its translation key (the others: TEXT)
Counter.LINE_COLOURS = {
    IGUI_LWT_Meter_Water_tainted = Counter.AMBER,
    IGUI_LWT_Meter_Water_fuel = Counter.AMBER,
}

-- The n digits (strings) of the whole part of `value` (nil or below 0: 0), keeping the last n.
function Counter.digits(value, n)
    local v = math.floor(math.max(0, tonumber(value) or 0))
    local out = {}
    for i = n, 1, -1 do
        local d = v % 10
        out[i] = string.format("%d", d)
        v = (v - d) / 10
    end
    return out
end

-- Angle of the hand in degrees for a reading: one turn every HAND_LITRES litres.
function Counter.handAngle(value)
    local v = math.max(0, tonumber(value) or 0)
    return (v % Counter.HAND_LITRES) / Counter.HAND_LITRES * 360
end

local textures = {}

-- Texture of a path, read once (false when the file is missing).
local function texture(path)
    if textures[path] == nil then textures[path] = getTexture(path) or false end
    return textures[path] or nil
end

-- Forget the textures read, so that new images are looked up again.
function Counter.reload()
    textures = {}
end

local function measure(font, s)
    return getTextManager():MeasureStringX(font, s)
end

local function height(font)
    return getTextManager():getFontHeight(font)
end

-- Lines under the dial: { text, colour }.
local function lines(view)
    local out = { { getText("IGUI_LWT_Meter_Total", string.format("%d", math.floor(view.reading or 0))), Counter.TEXT } }
    local keys = view.keys or {}
    for i = 1, #view.lines do
        out[#out + 1] = { view.lines[i], Counter.LINE_COLOURS[keys[i]] or Counter.TEXT }
    end
    return out
end

-- Width and height of the dial (or of the plain rolls without its texture).
local function dialSize()
    if texture(Counter.FACE_TEXTURE) then return Counter.DIAL, Counter.DIAL end
    return Counter.DIAL, Counter.PLAIN_ROLLS_H
end

function Counter.size(view)
    local w, h = dialSize()
    local list, lh = lines(view), height(UIFont.Small) + Counter.LINE_GAP
    for i = 1, #list do w = math.max(w, measure(UIFont.Small, list[i][1])) end
    return w, h + Counter.LINE_GAP * 2 + #list * lh
end

local function rect(ui, x, y, w, h, c, a)
    ui:drawRect(x, y, w, h, a or 1, c[1], c[2], c[3])
end

-- The digits in the box x, y, w, h: one roll each (cream, the last orange), shaded at the top and
-- the bottom like a drum, a thin gap between two rolls.
local function drawRolls(ui, digits, x, y, w, h)
    local rw, font = w / #digits, UIFont.Medium
    local fh, band = height(font), math.max(1, math.floor(h / 6))
    for i = 1, #digits do
        local last = i == #digits
        local bg = last and Counter.LAST_ROLL or Counter.ROLL
        local c = last and Counter.LAST_DIGIT or Counter.DIGIT
        local rx = x + (i - 1) * rw
        rect(ui, rx + 1, y, rw - 2, h, bg)
        rect(ui, rx + 1, y, rw - 2, band, Counter.CASE, Counter.SHADE)
        rect(ui, rx + 1, y + h - band, rw - 2, band, Counter.CASE, Counter.SHADE)
        ui:drawTextCentre(digits[i], rx + rw / 2, y + (h - fh) / 2, c[1], c[2], c[3], 1, font)
    end
end

function Counter.draw(ui, view, x, y)
    local face, hand = texture(Counter.FACE_TEXTURE), texture(Counter.HAND_TEXTURE)
    local dw, dh = dialSize()
    local digits = Counter.digits(view.reading, Counter.ROLLS)
    if face then
        ui:drawTextureScaled(face, x, y, dw, dh, 1, 1, 1, 1)
        local b = Counter.ROLLS_BOX
        drawRolls(ui, digits, x + b.x * dw, y + b.y * dh, b.w * dw, b.h * dh)
        if hand then
            ui:DrawTextureAngle(hand, x + Counter.HAND.x * dw, y + Counter.HAND.y * dh, Counter.handAngle(view.reading))
        end
    else
        rect(ui, x, y, dw, dh, Counter.CASE)
        drawRolls(ui, digits, x, y, dw, dh)
    end
    local list, lh = lines(view), height(UIFont.Small) + Counter.LINE_GAP
    local ly = y + dh + Counter.LINE_GAP * 2
    for i = 1, #list do
        local c = list[i][2]
        ui:drawText(list[i][1], x, ly + (i - 1) * lh, c[1], c[2], c[3], 1, UIFont.Small)
    end
end

Panels.register("counter", Counter)

return Counter
