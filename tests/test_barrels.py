"""E23: barrels connected to the house (ADR-001 D27, D28, L01-L03, L06, L07): a rain collector or barrel inside the
building or on its roof is connected with a pipe wrench to the inlet of that building, without pipe nor pump; by gravity
it serves its floor and the floors below, a LiveWater pump in the inlet's network or power on the barrel's square lifts
the rule; all the barrels of a house drain together, those kept in reserve last; an empty barrel stays connected; a
barrel holding anything but water gives nothing until emptied; Live Wire barrels are never taken."""
import unittest

from lwt_fakes import services
from lwt_harness import new_lua
from test_inlet import BENCH, INLET, POND, TILE

API = "shared/LiveWater/LWT_API.lua"

PLAN = r"""
Reserve = require("LiveWater/LWT_Reserve")
function plan(sources, needs)
    local moves, reasons = Reserve.plan(sources, needs)
    local by = {}
    for _, m in ipairs(moves) do by[m.source .. ">" .. m.need] = (by[m.source .. ">" .. m.need] or 0) + m.litres end
    return by, reasons
end
"""

BARRELS = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end
PLUMB.barrels = {}
function FakePlumbing:addBarrel(x, y, z, amount, extra)
    local b = { amount = amount or 0, capacity = 400, waterOnly = true }
    for f, v in pairs(extra or {}) do b[f] = v end
    self.barrels[k(x, y, z)] = b
    return b
end
function FakePlumbing:barrel(x, y, z)
    if self.unloaded[k(x, y, z)] then return nil, false end
    local b = self.barrels[k(x, y, z)]
    if not b or b.liveWire then return nil, true end
    return { amount = b.amount, capacity = b.capacity, waterOnly = b.waterOnly, mark = b.mark }, true
end
function FakePlumbing:markBarrel(x, y, z, mark)
    local b = self.barrels[k(x, y, z)]
    if b then b.mark = mark end
end
function FakePlumbing:transfer(bx, by, bz, rx, ry, rz, litres)
    local b, r = self.barrels[k(bx, by, bz)], self.relays[k(rx, ry, rz)]
    local n = math.min(litres, b.amount, r.capacity - r.amount)
    b.amount, r.amount = b.amount - n, r.amount + n
    return n
end
PUMPED = {}
-- No square has power unless a test says so (WORLD.unpowered = {}).
WORLD.unpowered = setmetatable({}, { __index = function() return true end })
BARRELS = require("LiveWater/LWT_HouseBarrels").new({ store = STORE, plumbing = PLUMB, world = WORLD, relays = RELAYS,
    lifted = function(part) return PUMPED[part.x .. "," .. part.y .. "," .. part.z] == true end })
CLOCK.chores = { RELAYS, BARRELS }
LiveWater.Events.on("partRemoved", function(entry) BARRELS:forget(entry) end)
-- Two floors served: a fixture on the ground floor (2, 12, 0) and one upstairs (6, 16, 1).
PLUMB:addFixture(2, 12, 0) PLUMB:addFixture(6, 16, 1)
place("LiveWater:HouseInlet", 5, 9, "batman_livewater_01_42")
function barrelAt(x, y, z) return PLUMB.barrels[x .. "," .. y .. "," .. z] end
"""

COMMANDS = r"""
CMDS = require("LiveWater/LWT_Commands").new({ topology = TOPO, catalog = LiveWater.Parts, world = WORLD, players = PLAYERS,
    barrels = BARRELS })
CMDS:register("connectBarrel", require("LiveWater/Commands/LWT_CmdConnectBarrel"))
CMDS:register("disconnectBarrel", require("LiveWater/Commands/LWT_CmdDisconnectBarrel"))
CMDS:register("reserveBarrel", require("LiveWater/Commands/LWT_CmdReserveBarrel"))
P = newPlayer(3, 13, 0, {}, { ["base:pipewrench"] = true })
function cmd(name, x, y, z) return CMDS:dispatch(P, name, { x = x, y = y, z = z }) end
"""


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


def bench():
    lua = services(new_lua, INLET, POND)
    lua.execute(BENCH)
    lua.execute(BARRELS)
    return lua


class SharedReserve(unittest.TestCase):
    def setUp(self):
        self.lua = new_lua(API)
        self.lua.execute(PLAN)

    def by(self, sources, needs):
        moves, reasons = self.lua.eval("{ plan(%s, %s) }" % (sources, needs)).values()
        return dict(moves.items()), reasons

    def test_the_barrels_drain_together_by_their_share(self):
        moves, _ = self.by('{ { key = "a", z = 0, amount = 30, usable = true }, { key = "b", z = 0, amount = 10, usable = true } }',
                           '{ { key = "r", z = 1, free = 20 } }')
        self.assertEqual(moves, {"a>r": 15, "b>r": 5})

    def test_a_barrel_in_reserve_is_taken_last(self):
        moves, _ = self.by('{ { key = "a", z = 0, amount = 5, usable = true },'
                           ' { key = "b", z = 0, amount = 100, usable = true, reserve = true } }',
                           '{ { key = "r", z = 1, free = 20 } }')
        self.assertEqual(moves, {"a>r": 5, "b>r": 15})

    def test_gravity_serves_the_barrel_floor_and_below_unless_lifted(self):
        moves, reasons = self.by('{ { key = "a", z = 0, amount = 50, usable = true } }',
                                 '{ { key = "low", z = 1, free = 10 }, { key = "up", z = 2, free = 10 } }')
        self.assertEqual(moves, {"a>low": 10})
        self.assertEqual(reasons[2], "gravity")
        moves, _ = self.by('{ { key = "a", z = 0, amount = 50, usable = true, lifted = true } }',
                           '{ { key = "up", z = 2, free = 10 } }')
        self.assertEqual(moves, {"a>up": 10})

    def test_a_barrel_holding_something_else_gives_nothing(self):
        moves, reasons = self.by('{ { key = "a", z = 0, amount = 50, usable = false } }',
                                 '{ { key = "r", z = 1, free = 10 } }')
        self.assertEqual(moves, {})
        self.assertEqual(reasons[1], "empty")


class Connection(unittest.TestCase):
    def test_a_barrel_in_the_house_or_on_its_roof_connects_to_its_inlet(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 0) PLUMB:addBarrel(4, 14, 5, 0) PLUMB:addBarrel(30, 30, 0, 0)")
        self.assertEqual(call(lua, "BARRELS:connect(3, 13, 0)"), (True, None))
        self.assertEqual(lua.eval("barrelAt(3, 13, 0).mark.inlet"), "5,9,0")
        self.assertEqual(call(lua, "BARRELS:connect(4, 14, 5)"), (True, None))
        self.assertEqual(call(lua, "BARRELS:connect(30, 30, 0)"), (False, "no_inlet"))
        self.assertEqual(call(lua, "BARRELS:connect(31, 30, 0)"), (False, "not_barrel"))

    def test_a_live_wire_barrel_is_never_taken(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 50, { liveWire = true })")
        self.assertEqual(call(lua, "BARRELS:connect(3, 13, 0)"), (False, "not_barrel"))

    def test_the_commands_check_the_wrench_and_the_reach(self):
        lua = bench()
        lua.execute(COMMANDS)
        lua.execute("PLUMB:addBarrel(3, 13, 0, 0)")
        lua.execute("P.tools = {}")
        self.assertEqual(call(lua, 'cmd("connectBarrel", 3, 13, 0)'), (False, "need_tool"))
        lua.execute('P.tools = { ["base:pipewrench"] = true } P.x = 20')
        self.assertEqual(call(lua, 'cmd("connectBarrel", 3, 13, 0)'), (False, "too_far"))
        lua.execute("P.x = 3")
        self.assertTrue(lua.eval('cmd("connectBarrel", 3, 13, 0)'))
        self.assertTrue(lua.eval('cmd("reserveBarrel", 3, 13, 0)'))
        self.assertTrue(lua.eval("barrelAt(3, 13, 0).mark.reserve"))
        self.assertTrue(lua.eval('cmd("disconnectBarrel", 3, 13, 0)'))
        self.assertIsNone(lua.eval("barrelAt(3, 13, 0).mark"))


class Menu(unittest.TestCase):
    def test_the_barrel_menu_follows_the_mirrored_connection(self):
        lua = new_lua(API)
        lua.execute('ISWorldObjectContextMenu = {} Events.OnFillWorldObjectContextMenu = { Add = function() end }'
                    ' M = require("LiveWater/LWT_BarrelMenu")')
        self.assertEqual(lua.eval("M.options(nil)[1][2]"), "connectBarrel")
        self.assertEqual(lua.eval("M.options({ inlet = '5,9,0' })[1][1]"), "ContextMenu_LWT_ReserveBarrel")
        self.assertEqual(lua.eval("M.options({ inlet = '5,9,0', reserve = true })[1][1]"), "ContextMenu_LWT_UseBarrel")
        self.assertEqual(lua.eval("M.options({ inlet = '5,9,0' })[2][2]"), "disconnectBarrel")


class Supply(unittest.TestCase):
    def test_a_ground_floor_barrel_fills_the_ground_floor_relays_without_a_pump(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 100) BARRELS:connect(3, 13, 0) CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).amount"), 25)
        self.assertEqual(lua.eval("relayAt(6, 16, 2).amount"), 0)
        self.assertEqual(lua.eval("barrelAt(3, 13, 0).amount"), 75)

    def test_a_pump_in_the_network_or_power_on_the_barrel_lifts_the_water(self):
        lua = bench()
        lua.execute('PLUMB:addBarrel(3, 13, 0, 100) BARRELS:connect(3, 13, 0) PUMPED["5,9,0"] = true CLOCK:tick()')
        self.assertEqual(lua.eval("relayAt(6, 16, 2).amount"), 25)
        lua = bench()
        lua.execute('PLUMB:addBarrel(3, 13, 0, 100) BARRELS:connect(3, 13, 0) CLOCK:tick()')
        self.assertEqual(lua.eval("relayAt(6, 16, 2).amount"), 0)
        lua.execute('WORLD.unpowered = {} CLOCK:tick()')
        self.assertEqual(lua.eval("relayAt(6, 16, 2).amount"), 25)

    def test_a_roof_barrel_serves_every_floor_below(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(4, 14, 5, 100) BARRELS:connect(4, 14, 5)")
        lua.execute('WORLD.unpowered["4,14,5"] = true CLOCK:tick()')
        self.assertEqual(lua.eval("relayAt(2, 12, 1).amount + relayAt(6, 16, 2).amount"), 50)

    def test_an_empty_barrel_stays_connected_and_a_gone_one_is_dropped(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 0) BARRELS:connect(3, 13, 0) CLOCK:tick()")
        self.assertEqual(lua.eval("barrelAt(3, 13, 0).mark.inlet"), "5,9,0")
        lua.execute('PLUMB.barrels["3,13,0"] = nil CLOCK:tick()')
        self.assertIsNone(lua.eval('next(STORE.barrels["5,9,0"] or {})'))

    def test_removing_the_inlet_disconnects_its_barrels(self):
        lua = bench()
        lua.execute("PLUMB:addBarrel(3, 13, 0, 10) BARRELS:connect(3, 13, 0) TOPO:remove(5, 9, 0)")
        self.assertIsNone(lua.eval("barrelAt(3, 13, 0).mark"))


if __name__ == "__main__":
    unittest.main()
