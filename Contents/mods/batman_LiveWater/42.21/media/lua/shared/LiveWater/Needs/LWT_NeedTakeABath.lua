-- LiveWater: fixture need of the mod Take a Bath and Shower (id TakeABathAndShowerNew), ADR-022 D03.
-- Its shower draws, little by little, up to its sandbox option ShowerConsumeWater (80 L by default)
-- and stops when the tap runs dry (TABAS_TakeShower.lua); its bathtub fills its own tub from the tap
-- up to TubWaterCapacity (200 L by default, TABAS_STubFluidContainer.lua). The relay above must hold
-- that much at once. Showers and bathtubs are recognised by the mod's own functions (TABAS_Iso).
-- Asked only when the mod is loaded: its sandbox options exist (read through getSandboxOptions,
-- as LWT_GameSettings does).

require "LiveWater/LWT_API"

local function option(name)
    local o = getSandboxOptions():getOptionByName("TakeABathAndShower." .. name)
    return o and tonumber(o:getValue()) or nil
end

local function need(obj)
    local shower, tub = option("ShowerConsumeWater"), option("TubWaterCapacity")
    if not shower and not tub then return nil end
    local Iso = require "TABAS_Iso"
    if type(Iso) ~= "table" then return nil end
    local litres = 0
    if shower and Iso.isShowerObject(obj, true) then litres = math.max(litres, shower) end
    if tub and Iso.isBathObject(obj) then litres = math.max(litres, tub) end
    if litres > 0 then return litres end
    return nil
end

LiveWater.API.registerFixtureNeed("LiveWater:TakeABathAndShower", need)
