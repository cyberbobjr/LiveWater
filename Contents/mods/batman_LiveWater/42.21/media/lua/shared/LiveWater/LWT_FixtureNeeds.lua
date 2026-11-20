-- LiveWater: registry of the fixture need providers (ADR-022 D01). A provider is a function given
-- a water fixture of the game (sink, shower, bathtub...) that returns the litres it must find in its
-- tank at once, or nil. LiveWater's own and the other mods' (LiveWater.API.registerFixtureNeed)
-- live here; the core never names a mod nor a kind of fixture.
--   register(id, fn) -> true, or false and "registration_closed", "invalid_id", "invalid_provider",
--                       "duplicate_provider"
--   seal()           no registration after the global ModData init
--   need(obj)        largest positive number the providers give for `obj`, or nil

local FixtureNeeds = {}
FixtureNeeds.__index = FixtureNeeds

function FixtureNeeds.new()
    return setmetatable({ providers = {}, ids = {}, sealed = false }, FixtureNeeds)
end

function FixtureNeeds:register(id, fn)
    if self.sealed then return false, "registration_closed" end
    if type(id) ~= "string" or id == "" then return false, "invalid_id" end
    if type(fn) ~= "function" then return false, "invalid_provider" end
    if self.providers[id] then return false, "duplicate_provider" end
    self.providers[id] = fn
    self.ids[#self.ids + 1] = id
    table.sort(self.ids)
    return true
end

function FixtureNeeds:seal()
    self.sealed = true
end

function FixtureNeeds:need(obj)
    local best
    for i = 1, #self.ids do
        local litres = self.providers[self.ids[i]](obj)
        if type(litres) == "number" and litres > 0 and (best == nil or litres > best) then best = litres end
    end
    return best
end

return FixtureNeeds
