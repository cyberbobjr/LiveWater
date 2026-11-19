"""ADR-013: the fill fitting (internal id LiveWater:BarrelFitting) under its new name in every language (D01), with a
tooltip on its item (D02); a vanilla feeding trough set against it is filled with tainted water, its water drawing
follows the level (D03); a trough holding feed has no water tank: nothing is poured and the information says so (D04).
Multi-tile troughs keep their tank on the master tile (IsoFeedingTrough.getMasterTrough, Java 42.22): a fitting
against any tile fills the master."""
import json
import os
import re
import unittest

from lwt_fakes import services
from lwt_harness import ROOT, new_lua
from test_fitting import BENCH, FITTING, POND

API = "shared/LiveWater/LWT_API.lua"
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
LANGS = ("CN", "DE", "EN", "ES", "FR", "JP", "KO", "PT", "PTBR", "RU", "TR")

# Game objects of the containers adapter (LWT_GameContainers): a vanilla trough (IsoFeedingTrough) with its water
# tank (FluidContainer, water and tainted water only), or with feed (no tank, an item container); a slave tile of a
# double trough points at its master.
GAME = r"""
Fluid = { Water = "Water", TaintedWater = "TaintedWater", Petrol = "Petrol" }
FluidType = { Water = "FT_Water", TaintedWater = "FT_TaintedWater", Petrol = "FT_Petrol" }
OBJ = {}
CALLS = {}
local function call(name) CALLS[#CALLS + 1] = name end
function tank(capacity, water, tainted)
    local fc = { capacity = capacity, fluids = { Water = water or 0, TaintedWater = tainted or 0 } }
    function fc:getCapacity() return self.capacity end
    function fc:getAmount() return self.fluids.Water + self.fluids.TaintedWater end
    function fc:getFreeCapacity() return self.capacity - self:getAmount() end
    function fc:getSpecificFluidAmount(f) return self.fluids[f] or 0 end
    function fc:addFluid(f, n) call("addFluid") self.fluids[f] = (self.fluids[f] or 0) + n end
    function fc:removeFluid(n)
        call("removeFluid")
        local a = self:getAmount()
        for k, v in pairs(self.fluids) do self.fluids[k] = v - v * n / a end
    end
    return fc
end
function trough(sprite, fc, items, master)
    local t = { trough = true, fc = fc, items = items or 0, master = master, sprite = sprite }
    function t:getSprite() return nil end
    function t:getSpriteName() return self.sprite end
    function t:getUsesExternalWaterSource() return false end
    function t:hasModData() return false end
    function t:getEntityScript() return nil end
    function t:getFluidContainer() return self.fc end
    function t:getContainer()
        if self.fc then return nil end
        local n = self.items
        return { isEmpty = function() return n == 0 end }
    end
    function t:getMasterTrough() return self.master or self end
    function t:addWater(ft, n) call("addWater:" .. ft) self.fc.fluids[ft == "FT_Water" and "Water" or "TaintedWater"] = self.fc.fluids[ft == "FT_Water" and "Water" or "TaintedWater"] + n end
    function t:removeWater(n) call("removeWater") self.fc:removeFluid(n) end
    function t:checkOverlayAfterAnimalEat() call("overlay") end
    function t:sendSyncEntity() call("syncEntity") end
    function t:sync() call("sync") end
    return t
end
function instanceof(obj, class) return class == "IsoFeedingTrough" and obj.trough == true end
function getCell() return { getGridSquare = function(_, x, y, z)
    local objs = OBJ[x .. "," .. y] or {}
    return { getObjects = function() return { size = function() return #objs end, get = function(_, i) return objs[i + 1] end } end }
end } end
GC = require("LiveWater/LWT_GameContainers").new({ registry = LiveWater.Containers, listed = function() return {} end })
"""


def game():
    lua = new_lua(API, "server/LiveWater/LWT_GameContainers.lua")
    lua.execute(GAME)
    return lua


class Trough(unittest.TestCase):
    def test_a_trough_with_its_tank_is_a_container(self):
        lua = game()
        lua.execute('OBJ["0,0"] = { trough("location_farm_trough_0", tank(100, 0, 20)) }')
        c = lua.eval("GC:at(0, 0, 0)")
        self.assertEqual((c.fluid, c.amount, c.free), ("tainted", 20, 80))
        self.assertIsNone(c.blocked)

    def test_the_water_poured_goes_in_the_vanilla_way_and_the_drawing_follows(self):
        lua = game()
        lua.execute('T = trough("location_farm_trough_0", tank(100, 0, 90)) OBJ["0,0"] = { T }')
        self.assertEqual(lua.eval('GC:add(0, 0, 0, 30, "tainted")'), 10)
        self.assertEqual(lua.eval("T.fc:getAmount()"), 100)
        calls = list(lua.eval("CALLS").values())
        self.assertIn("addWater:FT_TaintedWater", calls)
        self.assertIn("syncEntity", calls)
        self.assertNotIn("addFluid", calls)

    def test_water_taken_out_updates_the_drawing(self):
        lua = game()
        lua.execute('T = trough("location_farm_trough_0", tank(100, 50, 0)) OBJ["0,0"] = { T }')
        self.assertEqual(lua.eval("GC:take(0, 0, 0, 20)"), 20)
        calls = list(lua.eval("CALLS").values())
        self.assertIn("removeWater", calls)
        self.assertIn("overlay", calls)
        self.assertAlmostEqual(lua.eval("T.fc:getAmount()"), 30)

    def test_any_tile_of_a_long_trough_fills_its_master(self):
        lua = game()
        lua.execute('M = trough("location_farm_trough_1", tank(150, 0, 0)) OBJ["1,0"] = { M }'
                    ' OBJ["0,0"] = { trough("location_farm_trough_0", nil, 0, M) }')
        self.assertEqual(lua.eval("GC:at(0, 0, 0).free"), 150)
        self.assertEqual(lua.eval('GC:add(0, 0, 0, 40, "tainted")'), 40)
        self.assertEqual(lua.eval("M.fc:getAmount()"), 40)

    def test_a_trough_holding_feed_takes_nothing(self):
        lua = game()
        lua.execute('T = trough("location_farm_trough_0", nil, 3) OBJ["0,0"] = { T }')
        c = lua.eval("GC:at(0, 0, 0)")
        self.assertEqual((c.blocked, c.amount, c.free), ("feed", 0, 0))
        self.assertEqual(lua.eval('GC:add(0, 0, 0, 30, "tainted")'), 0)
        self.assertEqual(len(lua.eval("CALLS")), 0)


class FittingAgainstFeed(unittest.TestCase):
    def test_no_water_and_the_information_says_the_trough_holds_feed(self):
        lua = services(new_lua, POND, FITTING)
        lua.execute(BENCH)
        lua.execute(r"""
        local at = CONTAINERS.at
        function CONTAINERS:at(x, y, z)
            if FEED then return { blocked = "feed", amount = 0, free = 0 } end
            return at(self, x, y, z)
        end
        FEED = true CONT["2,-1"] = { amount = 0, capacity = 100 }
        tick()
        """)
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 0)
        self.assertEqual(lua.eval("#emitted('waterDelivered')"), 0)
        lines = [l[1] for l in lua.eval("LiveWater.Parts:lines(FIT)").values()]
        self.assertEqual(lines, ["IGUI_LWT_Fitting_TroughFeed"])
        # the feed eaten, the tank is back: the filling starts again
        lua.execute("FEED = false tick()")
        self.assertEqual(lua.eval('CONT["2,-1"].amount'), 50)


def load(lang, name):
    with open(os.path.join(MEDIA, "lua", "shared", "Translate", lang, name), encoding="utf-8") as f:
        return json.load(f)


NAMES = {"EN": "Fill Fitting", "FR": "Raccord de remplissage", "DE": "Füllanschluss", "ES": "Racor de llenado",
         "PT": "Conexão de enchimento", "PTBR": "Conexão de enchimento",
         "RU": "Заливной штуцер",
         "TR": "Doldurma Bağlantısı", "CN": "注水接头", "JP": "給水継手",
         "KO": "급수 연결구"}


class Texts(unittest.TestCase):
    def test_the_new_name_in_every_language(self):
        for lang in LANGS:
            with self.subTest(language=lang):
                self.assertEqual(load(lang, "ItemName.json")["Base.Mov_LiveWater_BarrelFitting"], NAMES[lang])
                self.assertEqual(load(lang, "Moveables.json")["Live_Water_Barrel_Fitting"], NAMES[lang])
                recipes = load(lang, "Recipes.json")
                for key in ("LWTBuildBarrelFitting", "LWTDismantleBarrelFitting"):
                    self.assertIn(NAMES[lang].lower(), recipes[key].lower(), key)

    def test_the_item_carries_its_tooltip_in_every_language(self):
        with open(os.path.join(MEDIA, "scripts", "LWT_moveables.txt"), encoding="ascii") as f:
            self.assertRegex(f.read(), r"item Mov_LiveWater_BarrelFitting\s*\{[^}]*Tooltip = Tooltip_LWT_FillFitting,")
        for lang in LANGS:
            with self.subTest(language=lang):
                self.assertTrue(load(lang, "Tooltip.json").get("Tooltip_LWT_FillFitting", "").strip())
        self.assertEqual(load("FR", "Tooltip.json")["Tooltip_LWT_FillFitting"],
                         "Se pose entre un tuyau et un baril, un récupérateur d'eau de pluie ou une mangeoire : "
                         "le réseau le remplit.")

    def test_the_trough_feed_line_in_every_language(self):
        for lang in LANGS:
            with self.subTest(language=lang):
                self.assertTrue(load(lang, "IG_UI.json").get("IGUI_LWT_Fitting_TroughFeed", "").strip())


if __name__ == "__main__":
    unittest.main()
