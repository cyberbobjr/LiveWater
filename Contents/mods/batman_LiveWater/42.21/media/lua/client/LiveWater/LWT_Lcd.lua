-- LiveWater: backlit LCD screen of the part windows, client (ADR-008 D07). LiveWater's own module
-- (the look follows Live Wire's device screens; LiveWater never needs Live Wire): a dark bezel, a
-- blue backlit screen, a glare line, dark ink.
-- The screen font is Code, except in the languages whose glyphs Code lacks (Chinese, Japanese,
-- Korean, Thai): Small there, which has them.

local Lcd = {}

Lcd.BEZEL = { 0.06, 0.07, 0.06 }
Lcd.SCREEN = { 0.38, 0.64, 0.82 }
Lcd.INK = { 0.05, 0.11, 0.20 }
Lcd.GLARE = { 0.96, 0.95, 0.90 }
Lcd.GLARE_ALPHA = 0.16
-- Thickness of the bezel, space between the screen's edge and its text, between two lines.
Lcd.BEZEL_SIZE = 5
Lcd.INSET = 8
Lcd.LINE_GAP = 4
-- Languages (Translator language names) whose glyphs the Code font does not have.
Lcd.NO_CODE_FONT = { CH = true, CN = true, JP = true, KO = true, TH = true }

-- Name of the UIFont of a screen in the language `lang`: "Code" or "Small".
function Lcd.fontFor(lang)
    if Lcd.NO_CODE_FONT[lang] then return "Small" end
    return "Code"
end

local function language()
    local lang = Translator and Translator.getLanguage and Translator.getLanguage()
    return lang and tostring(lang:name()) or ""
end

local fontCache = nil

-- UIFont of the screens (the language is read once).
function Lcd.font()
    if not fontCache then fontCache = UIFont[Lcd.fontFor(language())] or UIFont.Small end
    return fontCache
end

-- Height of one line of the screen.
function Lcd.lineHeight()
    return getTextManager():getFontHeight(Lcd.font()) + Lcd.LINE_GAP
end

-- Width and height of a screen showing `lines` (list of strings), bezel included.
function Lcd.size(lines)
    local tm, font, wide = getTextManager(), Lcd.font(), 0
    for i = 1, #lines do wide = math.max(wide, tm:MeasureStringX(font, lines[i])) end
    local pad = Lcd.BEZEL_SIZE + Lcd.INSET
    return wide + 2 * pad, math.max(1, #lines) * Lcd.lineHeight() - Lcd.LINE_GAP + 2 * pad
end

local function rect(ui, x, y, w, h, c, a)
    ui:drawRect(x, y, w, h, a or 1, c[1], c[2], c[3])
end

-- The screen at x, y (outer box w x h) with its lines.
function Lcd.draw(ui, lines, x, y, w, h)
    local b = Lcd.BEZEL_SIZE
    rect(ui, x, y, w, h, Lcd.BEZEL)
    rect(ui, x + b, y + b, w - 2 * b, h - 2 * b, Lcd.SCREEN)
    rect(ui, x + b + 2, y + b + 2, w - 2 * b - 4, 2, Lcd.GLARE, Lcd.GLARE_ALPHA)
    local font, lh, ink = Lcd.font(), Lcd.lineHeight(), Lcd.INK
    local tx, ty = x + b + Lcd.INSET, y + b + Lcd.INSET
    for i = 1, #lines do
        ui:drawText(lines[i], tx, ty + (i - 1) * lh, ink[1], ink[2], ink[3], 1, font)
    end
end

return Lcd
