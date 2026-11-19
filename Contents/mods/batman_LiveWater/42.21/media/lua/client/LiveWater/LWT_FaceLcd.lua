-- LiveWater: window face "lcd" (ADR-008 D07): the information lines of the part on a backlit LCD
-- screen (LWT_Lcd). Declared by the pump (`panel` hook); any part may ask for it.

local Lcd = require "LiveWater/LWT_Lcd"
local Panels = require "LiveWater/LWT_Panels"

local Face = {}

function Face.size(view)
    return Lcd.size(view.lines)
end

function Face.draw(ui, view, x, y)
    local w, h = Lcd.size(view.lines)
    Lcd.draw(ui, view.lines, x, y, w, h)
end

Panels.register("lcd", Face)

return Face
