"""E28: plumbed washing machines in multiplayer (ADR-001 L13, Q08), defects of 42.22 proved statically: the server stops
a washer that ran dry without telling the clients (ClothingWasherLogic.update), and a plain washer never sends its
plumbed state (IsoClothingWasher.saveChange). The fix only touches washers fed by LiveWater's relays, on a server, and a
sandbox option (on by default) turns it off."""
import os
import unittest

from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")

BENCH = r"""
local function k(x, y, z) return x .. "," .. y .. "," .. z end
-- Relays of one inlet, and the washers each one feeds.
RELAYS = { list = { { x = 2, y = 2, z = 1 } } }
function RELAYS:inlets() return { { x = 5, y = 9, z = 0 } } end
function RELAYS:positions(part) return self.list end
WASHERS = { ["2,2,0"] = { x = 2, y = 2, z = 0, activated = true, plain = true, marked = false } }
PLUMB = { sent = {}, marked = {} }
function PLUMB:washers(x, y, z)
    local out = {}
    for _, w in pairs(WASHERS) do
        if math.abs(w.x - x) <= 1 and math.abs(w.y - y) <= 1 and w.z == z - 1 then table.insert(out, w) end
    end
    return out
end
function PLUMB:sendWasherState(x, y, z) table.insert(self.sent, k(x, y, z)) end
function PLUMB:markWasher(x, y, z) table.insert(self.marked, k(x, y, z)) WASHERS[k(x, y, z)].marked = true end
ENABLED, SERVER = true, true
FIX = require("LiveWater/LWT_WasherFix").new({ relays = RELAYS, plumbing = PLUMB,
    enabled = function() return ENABLED end, multiplayer = function() return SERVER end })
"""


def bench():
    lua = new_lua(API, "server/LiveWater/LWT_WasherFix.lua")
    lua.execute(BENCH)
    return lua


class WasherFix(unittest.TestCase):
    def test_a_washer_stopped_by_the_server_is_told_to_the_clients_once(self):
        lua = bench()
        lua.execute("FIX:tick()")
        self.assertEqual(lua.eval("#PLUMB.sent"), 0)
        lua.execute('WASHERS["2,2,0"].activated = false FIX:tick() FIX:tick()')
        self.assertEqual(lua.eval("#PLUMB.sent"), 1)
        lua.execute('WASHERS["2,2,0"].activated = true FIX:tick() WASHERS["2,2,0"].activated = false FIX:tick()')
        self.assertEqual(lua.eval("#PLUMB.sent"), 2)

    def test_a_plain_washer_is_marked_plumbed_once(self):
        lua = bench()
        lua.execute("FIX:tick() FIX:tick()")
        self.assertEqual(lua.eval("#PLUMB.marked"), 1)

    def test_nothing_in_solo_nor_when_switched_off(self):
        lua = bench()
        lua.execute('SERVER = false WASHERS["2,2,0"].activated = false FIX:tick()')
        self.assertEqual(lua.eval("#PLUMB.sent + #PLUMB.marked"), 0)
        lua.execute("SERVER, ENABLED = true, false FIX:tick()")
        self.assertEqual(lua.eval("#PLUMB.sent + #PLUMB.marked"), 0)

    def test_the_client_applies_the_plumbed_mark(self):
        lua = new_lua(API)
        lua.execute(r"""
        SandboxVars = { LiveWater = { WasherFix = true } }
        function instanceof(o, c) return c == "IsoClothingWasher" and o.washer end
        function newWasher(marked)
            local o = { washer = true, ext = false, md = marked and { LiveWaterWasher = { plumbed = true } } or {} }
            function o:hasModData() return true end
            function o:getModData() return self.md end
            function o:getUsesExternalWaterSource() return self.ext end
            function o:setUsesExternalWaterSource(v) self.ext = v end
            return o
        end
        C = require("LiveWater/LWT_WasherClient")
        A, B = newWasher(true), newWasher(false)
        C.apply(A) C.apply(B)
        """)
        self.assertTrue(lua.eval("A.ext"))
        self.assertFalse(lua.eval("B.ext"))
        lua.execute("SandboxVars.LiveWater.WasherFix = false D = newWasher(true) C.apply(D)")
        self.assertFalse(lua.eval("D.ext"))

    def test_sandbox_option_on_by_default_and_incompatible_mods(self):
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="utf-8") as f:
            block = f.read().split("option LiveWater.WasherFix")[1].split("}")[0]
        self.assertIn("type = boolean", block)
        self.assertIn("default = true", block)
        with open(os.path.join(MEDIA, "..", "mod.info"), encoding="utf-8") as f:
            self.assertIn("incompatible=\\LGExtendedPlumbing,\\LGMainsWater", f.read())


if __name__ == "__main__":
    unittest.main()
