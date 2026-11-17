-- LiveWater: names shared by the client and the server for sendClientCommand and
-- sendServerCommand (module and command names). Arguments are always re-checked on the server.
--   client -> server  LAY { x, y, z, part }   DISMANTLE { x, y, z }
--                     FIT_FILTER { x, y, z }  REMOVE_FILTER { x, y, z }
--   server -> client  NOTICE { key }          (translation key of a refusal)

local Protocol = {
    MODULE = "LiveWater",
    LAY = "lay",
    DISMANTLE = "dismantle",
    FIT_FILTER = "fitFilter",
    REMOVE_FILTER = "removeFilter",
    NOTICE = "notice",
}

return Protocol
