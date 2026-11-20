-- LiveWater: registration of the part types that need current as Live Wire consumers (ADR-001 D20,
-- ADR-017 D01, D03), shared by the authority (LWT_Power) and a multiplayer client
-- (LWT_PowerClient): both sides register, so that Live Wire's menus of a client find the parts by
-- sprite. No game API, no event: the caller chooses the moment (OnInitWorld, before Live Wire seals
-- its registrations at OnInitGlobalModData).
--   usable(api)                      Live Wire's API has registerConsumer and revision 6 or later.
--   id(typeId)                       consumer id ("LiveWater:PondPump" -> "LiveWater_LiveWater_PondPump").
--   base(catalog, typeId, revision)  the definition both sides share: sprites, category, circuit,
--                                    and, from Live Wire revision 9, `link` when the part type
--                                    carries one (catalog data, Parts:linkOf).
--   register(api, catalog, complete) registers every part type whose capabilities need current
--                                    (`power` hook); complete(typeId, def) adds what the side owns
--                                    (powerConsumption, display, summary). Returns how many types are
--                                    registered and { [typeId] = definition } (nil and {} when the
--                                    API is not usable). A consumer already registered counts.

local Consumers = {}

Consumers.MIN_REVISION = 6
Consumers.LINK_REVISION = 9

function Consumers.usable(api)
    return type(api) == "table" and type(api.revision) == "number" and api.revision >= Consumers.MIN_REVISION
        and type(api.registerConsumer) == "function"
end

function Consumers.id(typeId)
    return "LiveWater_" .. string.gsub(typeId, ":", "_")
end

function Consumers.base(catalog, typeId, revision)
    local def = { sprites = catalog:spritesOf(typeId), category = "other", circuit = "equipment" }
    if revision >= Consumers.LINK_REVISION then def.link = catalog:linkOf(typeId) end
    return def
end

function Consumers.register(api, catalog, complete)
    local registered = {}
    if not Consumers.usable(api) then return 0, registered end
    local count, ids = 0, catalog:ids()
    for i = 1, #ids do
        local typeId = ids[i]
        if catalog:first({ type = typeId }, "power") then
            local def = Consumers.base(catalog, typeId, api.revision)
            complete(typeId, def)
            local ok, reason = api.registerConsumer(Consumers.id(typeId), def)
            if ok or reason == "duplicate_consumer" then
                registered[typeId] = def
                count = count + 1
            else
                print("LiveWater: Live Wire consumer " .. typeId .. " not registered: " .. tostring(reason))
            end
        end
    end
    return count, registered
end

return Consumers
