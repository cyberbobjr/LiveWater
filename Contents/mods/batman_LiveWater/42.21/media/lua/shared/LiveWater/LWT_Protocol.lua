-- LiveWater: names shared by the client and the server for sendClientCommand and
-- sendServerCommand (module and command names). Arguments are always re-checked on the server.
--   client -> server  LAY { x, y, z, part }   DISMANTLE { x, y, z }
--                     FIT_FILTER { x, y, z }  REMOVE_FILTER { x, y, z }
--                     SWITCH_PUMP { x, y, z } REPAIR_PUMP { x, y, z }
--                     CONNECT_BARREL, DISCONNECT_BARREL, RESERVE_BARREL { x, y, z }
--                     CITY_WATER { x, y, z }
--                     SWITCH_VALVE { x, y, z }  SET_TIMER { x, y, z, hours }
--                     SHOW_NETWORK { x, y, z }  SWITCH_FITTING { x, y, z }
--                     REMOVE_ALL {} (admin: remove LiveWater from the world)
--   server -> client  NOTICE { key }          (translation key of a refusal)
--                     SOUND { x, y, z, name } (sound loop of a part: name, or nil to stop)
--                     NETWORK { parts = { { x, y, z } } } (squares of a network, to one player)
--                     JET { x, y, z }         (a sprinkler there started or stopped spraying:
--                                              the clients look at its mirrored state again)

local Protocol = {
    MODULE = "LiveWater",
    LAY = "lay",
    DISMANTLE = "dismantle",
    FIT_FILTER = "fitFilter",
    REMOVE_FILTER = "removeFilter",
    SWITCH_PUMP = "switchPump",
    REPAIR_PUMP = "repairPump",
    CONNECT_BARREL = "connectBarrel",
    DISCONNECT_BARREL = "disconnectBarrel",
    RESERVE_BARREL = "reserveBarrel",
    CITY_WATER = "cityWater",
    SWITCH_VALVE = "switchValve",
    SET_TIMER = "setTimer",
    SHOW_NETWORK = "showNetwork",
    SWITCH_FITTING = "switchFitting",
    REMOVE_ALL = "removeLiveWater",
    NETWORK = "network",
    JET = "jet",
    SOUND = "sound",
    NOTICE = "notice",
}

return Protocol
