-- LiveWater: names shared by the client and the server for sendClientCommand and
-- sendServerCommand (module and command names). Arguments are always re-checked on the server.
--   client -> server  FIT_FILTER { x, y, z }  REMOVE_FILTER { x, y, z }
--                     SWITCH_PUMP { x, y, z } REPAIR_PUMP { x, y, z }
--                     CITY_WATER { x, y, z }
--                     SWITCH_VALVE { x, y, z }  SET_TIMER { x, y, z, hours }
--                     SHOW_NETWORK { x, y, z }
--                     REMOVE_ALL {} (admin: remove LiveWater from the world)
--   server -> client  NOTICE { key }          (translation key of a refusal)
--                     SOUND { x, y, z, name, once } (sound loop of a part: name, or nil to stop;
--                     once = true: a one-shot sound, ADR-008 D10)
--                     NETWORK { parts = { { x, y, z } }, fixtures = { { x, y, z, status } } }
--                             (squares of a network and the fixtures of its inlets, to one player)
--                     JET { x, y, z }         (a sprinkler there started or stopped spraying:
--                                              the clients look at its mirrored state again)

local Protocol = {
    MODULE = "LiveWater",
    FIT_FILTER = "fitFilter",
    REMOVE_FILTER = "removeFilter",
    SWITCH_PUMP = "switchPump",
    REPAIR_PUMP = "repairPump",
    CITY_WATER = "cityWater",
    SWITCH_VALVE = "switchValve",
    SET_TIMER = "setTimer",
    SHOW_NETWORK = "showNetwork",
    REMOVE_ALL = "removeLiveWater",
    NETWORK = "network",
    JET = "jet",
    SOUND = "sound",
    NOTICE = "notice",
}

return Protocol
