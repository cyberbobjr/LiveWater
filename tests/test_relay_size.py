"""ADR-022: relay tanks sized to the fixtures they serve. Fixture need providers (LWT_FixtureNeeds, API
registerFixtureNeed, revision 25); a relay holds the largest need of the fixtures it serves, at least 25 L and at most
the sandbox option RelayMaxLitres (300 L by default); relays already placed are resized at the next survey; the
provider shipped for Take a Bath and Shower (shower: ShowerConsumeWater, bathtub: TubWaterCapacity)."""
import json
import os
import unittest

from lwt_harness import ROOT, new_lua, read
from test_inlet import TILE, bench

API = "shared/LiveWater/LWT_API.lua"
TABAS = "shared/LiveWater/Needs/LWT_NeedTakeABath.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
LANGS = ("CN", "DE", "EN", "ES", "FR", "JP", "KO", "PT", "PTBR", "RU", "TR")


class Registry(unittest.TestCase):
    def test_revision_25_offers_register_fixture_need(self):
        lua = new_lua(API)
        self.assertEqual(lua.eval("LiveWater.API.revision"), 25)
        self.assertTrue(lua.eval('LiveWater.API.registerFixtureNeed("Test:Shower", function(obj) return 80 end)'))

    def test_bad_registrations_are_refused(self):
        lua = new_lua(API)
        lua.execute('LiveWater.API.registerFixtureNeed("Test:A", function() return 1 end)')
        for call, reason in (('"", function() end', "invalid_id"), ('"Test:B", 12', "invalid_provider"),
                             ('"Test:A", function() end', "duplicate_provider")):
            t = lua.eval("{ LiveWater.API.registerFixtureNeed(%s) }" % call)
            self.assertEqual((t[1], t[2]), (False, reason), call)
        lua.execute("fire('OnInitGlobalModData')")
        t = lua.eval('{ LiveWater.API.registerFixtureNeed("Test:C", function() end) }')
        self.assertEqual((t[1], t[2]), (False, "registration_closed"))

    def test_the_need_is_the_largest_answer_and_nothing_without_one(self):
        lua = new_lua(API)
        lua.execute('LiveWater.API.registerFixtureNeed("Test:A", function(obj) return obj.a end)'
                    ' LiveWater.API.registerFixtureNeed("Test:B", function(obj) return obj.b end)')
        self.assertEqual(lua.eval("LiveWater.FixtureNeeds:need({ a = 80, b = 200 })"), 200)
        self.assertEqual(lua.eval("LiveWater.FixtureNeeds:need({ a = 80, b = 'x' })"), 80)
        self.assertIsNone(lua.eval("LiveWater.FixtureNeeds:need({ a = -3 })"))
        self.assertIsNone(lua.eval("LiveWater.FixtureNeeds:need({})"))


class Size(unittest.TestCase):
    def placed(self, *fixtures, settings=""):
        lua = bench()
        lua.execute(settings)
        for f in fixtures:
            lua.execute("PLUMB:addFixture(%s)" % f)
        lua.execute('place("LiveWater:HouseInlet", 5, 9, "%s42") CLOCK:tick()' % TILE)
        return lua

    def test_a_fixture_without_need_keeps_25_litres(self):
        lua = self.placed("2, 12, 0")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 25)

    def test_a_shower_gets_a_relay_of_its_need(self):
        lua = self.placed("2, 12, 0, true, 80")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 80)

    def test_a_shared_relay_takes_the_largest_need_of_its_fixtures(self):
        lua = self.placed("2, 12, 0, true, 80", "3, 12, 0, true, 200", "2, 13, 0")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 200)

    def test_a_need_below_25_litres_keeps_25(self):
        lua = self.placed("2, 12, 0, true, 5")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 25)

    def test_the_option_caps_the_size(self):
        self.assertEqual(self.placed("2, 12, 0, true, 2000").eval("relayAt(2, 12, 1).capacity"), 300)
        lua = self.placed("2, 12, 0, true, 200", settings="SETTINGS.RelayMaxLitres = 60")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 60)

    def test_a_relay_already_placed_is_resized_at_the_next_survey(self):
        lua = self.placed("2, 12, 0")
        lua.execute("relayAt(2, 12, 1).amount = 20 PLUMB.list[1].need = 80 RELAYS:touched(2, 12) CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 80)
        self.assertEqual(lua.eval("PLUMB.resized"), 1)
        lua.execute("CLOCK:tick()")
        self.assertEqual(lua.eval("PLUMB.resized"), 1)

    def test_a_lower_cap_shrinks_a_relay_and_loses_the_water_above(self):
        lua = self.placed("2, 12, 0, true, 200")
        lua.execute("relayAt(2, 12, 1).amount = 150 SETTINGS.RelayMaxLitres = 80 RELAYS:touched(2, 12) CLOCK:tick()")
        self.assertEqual(lua.eval("relayAt(2, 12, 1).capacity"), 80)
        self.assertLessEqual(lua.eval("relayAt(2, 12, 1).amount"), 80)

    def test_the_need_counts_in_the_inlet_demand(self):
        lua = self.placed("2, 12, 0, true, 80")
        self.assertEqual(lua.eval("OUTLETS:need(REG:at(5, 9, 0))"), 80)


TABAS_BENCH = r"""
OPTIONS = { ["TakeABathAndShower.ShowerConsumeWater"] = 80, ["TakeABathAndShower.TubWaterCapacity"] = 200 }
function getSandboxOptions()
    return { getOptionByName = function(self, name)
        local v = OPTIONS[name]
        if v == nil then return nil end
        return { getValue = function() return v end }
    end }
end
LWT_LOADED["TABAS_Iso"] = {
    isShowerObject = function(obj, allowedOnBath) return obj.shower or (allowedOnBath and obj.bathShower) or false end,
    isBathObject = function(obj) return obj.bath or obj.bathShower or false end,
}
"""


class TakeABathAndShower(unittest.TestCase):
    def lua(self, active=True):
        lua = new_lua(API)
        lua.execute(TABAS_BENCH)
        if not active:
            lua.execute("OPTIONS = {}")
        lua.execute(read(TABAS))
        return lua

    def test_a_shower_needs_the_water_of_one_shower(self):
        self.assertEqual(self.lua().eval("LiveWater.FixtureNeeds:need({ shower = true })"), 80)

    def test_a_bathtub_needs_its_tub(self):
        self.assertEqual(self.lua().eval("LiveWater.FixtureNeeds:need({ bath = true })"), 200)

    def test_a_bathtub_with_a_shower_takes_the_larger(self):
        lua = self.lua()
        lua.execute('OPTIONS["TakeABathAndShower.ShowerConsumeWater"] = 250')
        self.assertEqual(lua.eval("LiveWater.FixtureNeeds:need({ bathShower = true })"), 250)

    def test_a_sink_needs_nothing_more(self):
        self.assertIsNone(self.lua().eval("LiveWater.FixtureNeeds:need({})"))

    def test_without_the_mod_nothing_is_asked(self):
        lua = self.lua(active=False)
        lua.execute('LWT_LOADED["TABAS_Iso"] = nil')
        self.assertIsNone(lua.eval("LiveWater.FixtureNeeds:need({ shower = true })"))


class Option(unittest.TestCase):
    def test_the_cap_option_is_declared_with_its_translations(self):
        with open(os.path.join(MEDIA, "sandbox-options.txt"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("option LiveWater.RelayMaxLitres", text)
        block = text.split("option LiveWater.RelayMaxLitres", 1)[1].split("}", 1)[0]
        self.assertIn("min = 25", block)
        self.assertIn("max = 1000", block)
        self.assertIn("default = 300", block)
        for lang in LANGS:
            with open(os.path.join(MEDIA, "lua", "shared", "Translate", lang, "Sandbox.json"), encoding="utf-8") as f:
                keys = json.load(f)
            for key in ("Sandbox_LWT_RelayMaxLitres", "Sandbox_LWT_RelayMaxLitres_tooltip"):
                self.assertIn(key, keys, lang)


if __name__ == "__main__":
    unittest.main()
