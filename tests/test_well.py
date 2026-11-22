"""E17: a vanilla well as a clean source (ADR-001 D24, P02): the same pond pump set down next to a well (camping_01_16)
draws clean water; the intake reports the quality of the source kind it recorded; source kinds are data registered
through the public API (LiveWater.API.registerSource), natural water tainted, well clean."""
import json
import os
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
POND = "shared/LiveWater/Parts/LWT_PartPondPump.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")

BENCH = r"""
LiveWater.API.registerPart("Test:Inlet", { sprites = { [0] = "t_inlet" },
    capabilities = { outlet = { type = "houseInlet" } } })
NEED = {}
CLOCK = require("LiveWater/LWT_Clock").new({ network = NET, flow = require("LiveWater/LWT_Flow").new(LiveWater.Parts),
    catalog = LiveWater.Parts, world = WORLD, events = LiveWater.Events, sources = LiveWater.Sources,
    power = { powered = function() return true end },
    need = function(part) return NEED[part.x .. "," .. part.y] or 0 end })
function nextToWell(x, y) WORLD.dry[x .. "," .. y .. ",0"] = true WORLD.near[x .. "," .. y .. ",0"] = { camping_01_16 = true } end
"""


def bench():
    lua = services(new_lua, POND)
    lua.execute(BENCH)
    return lua


def call(lua, expr):
    t = lua.eval("{ %s }" % expr)
    return t[1], t[2]


class Well(unittest.TestCase):
    def test_a_pump_next_to_a_well_draws_clean_water_for_the_house(self):
        lua = bench()
        lua.execute('nextToWell(0, 0) place("LiveWater:PondPump", 0, 0) place("Test:Inlet", 1, 0)')
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.intake.source"), "well")
        lua.execute('NEED["1,0"] = 20 EMITTED = {} CLOCK:tick()')
        d = lua.eval('emitted("waterDelivered")')
        self.assertEqual((d[1][3], d[1][4]), (20, "clean"))
        lines = lua.eval("LiveWater.Parts:lines(REG:at(0, 0, 0))")
        self.assertIn("IGUI_LWT_Source_well", [l[1] for l in lines.values()])

    def test_the_well_wins_over_natural_water(self):
        lua = bench()
        lua.execute('WORLD.near["0,0,0"] = { camping_01_16 = true } place("LiveWater:PondPump", 0, 0)')
        self.assertEqual(lua.eval("REG:at(0, 0, 0).data.intake.source"), "well")

    def test_a_pump_next_to_a_hand_pump_draws_clean_water(self):
        # ADR-025: the game's metal hand pump (camping_01_64 to 67, one sprite per facing) is a well
        for sprite in ("camping_01_64", "camping_01_65", "camping_01_66", "camping_01_67"):
            lua = bench()
            lua.execute('WORLD.dry["0,0,0"] = true WORLD.near["0,0,0"] = { %s = true }' % sprite)
            lua.execute('place("LiveWater:PondPump", 0, 0) place("Test:Inlet", 1, 0)')
            self.assertEqual(lua.eval("REG:at(0, 0, 0).data.intake.source"), "well", sprite)
            lua.execute('NEED["1,0"] = 20 EMITTED = {} CLOCK:tick()')
            d = lua.eval('emitted("waterDelivered")')
            self.assertEqual((d[1][3], d[1][4]), (20, "clean"), sprite)

    def test_pond_water_stays_tainted(self):
        lua = bench()
        lua.execute('place("LiveWater:PondPump", 0, 0) place("Test:Inlet", 1, 0) NEED["1,0"] = 20 EMITTED = {} CLOCK:tick()')
        self.assertEqual(len(lua.eval('emitted("waterDelivered")')), 0)

    def test_neither_water_nor_well_is_refused(self):
        lua = bench()
        lua.execute('WORLD.dry["0,0,0"] = true')
        self.assertEqual(call(lua, 'place("LiveWater:PondPump", 0, 0)'), (False, "no_source"))


class RegisterSource(unittest.TestCase):
    def api(self):
        lua = new_lua(API)
        lua.execute("print = function() end")
        return lua

    def test_a_mod_adds_a_source_kind(self):
        lua = self.api()
        self.assertEqual(call(lua, 'LiveWater.API.registerSource("MyMod:Cistern", { quality = "clean", sprites = { "my_cistern_0" } })'),
                         (True, None))
        self.assertEqual(lua.eval('LiveWater.Sources:quality("MyMod:Cistern")'), "clean")
        self.assertEqual(lua.eval('LiveWater.Sources:quality("well")'), "clean")
        self.assertEqual(lua.eval('LiveWater.Sources:quality("water")'), "tainted")
        self.assertGreaterEqual(lua.eval("LiveWater.API.revision"), 6)

    def test_refusals(self):
        lua = self.api()
        self.assertEqual(call(lua, 'LiveWater.API.registerSource("well", { quality = "clean", sprites = { "x" } })'),
                         (False, "duplicate_source"))
        self.assertEqual(call(lua, 'LiveWater.API.registerSource("Bad Kind", { quality = "clean", flag = "water" })'),
                         (False, "invalid_kind"))
        self.assertEqual(call(lua, 'LiveWater.API.registerSource("MyMod:X", { quality = "salty", flag = "water" })'),
                         (False, "invalid_definition"))
        self.assertEqual(call(lua, 'LiveWater.API.registerSource("MyMod:Y", { quality = "clean" })'),
                         (False, "invalid_definition"))
        lua.execute('fire("OnInitGlobalModData", false)')
        self.assertEqual(call(lua, 'LiveWater.API.registerSource("MyMod:Z", { quality = "clean", flag = "water" })'),
                         (False, "registration_closed"))


class Texts(unittest.TestCase):
    def test_translations(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in ("EN", "FR"):
            with open(os.path.join(tr, lang, "IG_UI.json"), encoding="utf-8") as f:
                ui = json.load(f)
            self.assertIn("IGUI_LWT_Source_well", ui, lang)


if __name__ == "__main__":
    unittest.main()
