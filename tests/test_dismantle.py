"""ADR-007 D01-D03: every LiveWater equipment is dismantled in the inventory (recipe LWTDismantle<Part>) and every
placeable part except the drip line in the world (vanilla scrap, material LiveWater<Part>), both fed by the one table
LWT_Dismantle.lua. A dismantle never gives back more than the build cost, in degraded materials, and a part cut out of
a quarter of a raw material never gives a whole one back."""
import json
import os
import re
import sys
import unittest
from collections import defaultdict
from fractions import Fraction

from lwt_harness import ROOT, new_lua

MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")
SCRIPTS = os.path.join(MEDIA, "scripts")
DISMANTLE = "shared/LiveWater/LWT_Dismantle.lua"
SCRAP = "shared/LiveWater/LWT_GameScrap.lua"

# Weight of the vanilla materials a LiveWater part is built from or gives back
# (media/scripts/generated/items/normal.txt, Build 42.22), by family: what a dismantle gives back weighs at most what
# the build cost, family by family.
FAMILIES = {
    "metal": {"Base.MetalPipe": 1.5, "Base.ScrapMetal": 1.0, "Base.SmallSheetMetal": 0.5, "Base.Screws": 0.05,
              "Base.IronPiece": 0.1},
    "electronics": {"Base.ElectronicsScrap": 0.1, "Base.ElectricWire": 0.1},
    "cloth": {"Base.RippedSheets": 0.1},
    "rubber": {"Base.RubberHose": 0.3},
    "wood": {"Base.Plank": 3.0},
}
# Junk that no vanilla recipe uses: giving it back can never be turned into more material.
JUNK = {"Base.RubberBand"}
# Whole raw materials a quarter part is cut out of (ADR-007 D01).
RAW = {"Base.MetalPipe", "Base.RubberHose"}
# Worn items and the new item they were (ADR-009 D01): a worn one cost what the new one cost, and the recipe that
# turns it back into a new one is not a build recipe.
WORN = {"LiveWater.WaterFilterSpent": "LiveWater.WaterFilter"}


def family(item):
    for name, weights in FAMILIES.items():
        if item in weights:
            return name, weights[item]
    return None, None


def parse_recipes():
    """craftRecipe name -> {inputs: [(n, items|None, tags|None, keep)], outputs: [(n, item)], fields}."""
    recipes = {}
    for name in os.listdir(SCRIPTS):
        with open(os.path.join(SCRIPTS, name), encoding="ascii") as f:
            text = re.sub(r"/\*.*?\*/", "", f.read(), flags=re.S)
        for m in re.finditer(r"craftRecipe\s+(\w+)\s*\{(.*?)\n    \}", text, re.S):
            body = m.group(2)
            fields = dict(re.findall(r"^\s*(\w+)\s*=\s*([^,\n]+),", body, re.M))
            ins = re.search(r"inputs\s*\{(.*?)\}", body, re.S).group(1)
            outs = re.search(r"outputs\s*\{(.*?)\}", body, re.S).group(1)
            inputs = []
            for line in ins.strip().splitlines():
                n = int(re.match(r"\s*item\s+(\d+)", line).group(1))
                items = re.search(r"\[([^\]]+)\]", line)
                tags = re.search(r"tags\[([^\]]+)\]", line)
                inputs.append((n, None if tags else items.group(1).split(";"), tags.group(1).split(";") if tags else None,
                               "mode:keep" in line))
            outputs = [(int(n), it) for n, it in re.findall(r"item\s+(\d+)\s+([\w.]+)", outs)]
            recipes[m.group(1)] = {"inputs": inputs, "outputs": outputs, "fields": fields}
    return recipes


def equipment():
    """Full types of every LiveWater item: the moveables (module Base) and the inventory items (module LiveWater)."""
    out = []
    for name, module in (("LWT_moveables.txt", "Base"), ("LWT_items.txt", "LiveWater")):
        with open(os.path.join(SCRIPTS, name), encoding="ascii") as f:
            out += ["%s.%s" % (module, it) for it in re.findall(r"^\s*item\s+(\w+)", f.read(), re.M)]
    return out


def build_cost(item, recipes):
    """Raw materials consumed to make one `item`, LiveWater intermediates expanded (fractions for split outputs)."""
    if item in WORN:
        return build_cost(WORN[item], recipes)
    for name, r in recipes.items():
        if name.startswith("LWTDismantle"):
            continue
        if any(items and items[0] in WORN for _, items, _, _ in r["inputs"]):
            continue
        made = dict((it, n) for n, it in r["outputs"])
        if item not in made:
            continue
        cost = defaultdict(Fraction)
        for n, items, tags, keep in r["inputs"]:
            if keep:
                continue
            key = items[0] if items else "tags[%s]" % ";".join(tags)
            share = Fraction(n, made[item])
            if key.startswith("Base.Mov_LiveWater_") or key.startswith("LiveWater."):
                for k, v in build_cost(key, recipes).items():
                    cost[k] += v * share
            else:
                cost[key] += share
        return cost
    raise AssertionError("no build recipe for %s" % item)


def table(lua):
    d = lua.eval('require("LiveWater/LWT_Dismantle")')
    parts = []
    for i in range(1, len(d.PARTS) + 1):
        p = d.PARTS[i]
        returns = [(p.returns[j][1], int(p.returns[j][2])) for j in range(1, len(p.returns) + 1)]
        parts.append({"name": p.name, "item": p.item, "tool": p.tool, "time": p.time, "scrap": p.scrap,
                      "returns": returns, "recipe": d.recipeName(p), "material": d.material(p)})
    return d, parts


def lua_list(t):
    return [t[i] for i in range(1, len(t) + 1)]


class DismantleRecipes(unittest.TestCase):
    def setUp(self):
        self.lua = new_lua(DISMANTLE)
        self.d, self.parts = table(self.lua)
        self.recipes = parse_recipes()

    def test_every_equipment_has_one_entry_and_one_recipe(self):
        self.assertEqual(sorted(p["item"] for p in self.parts), sorted(equipment()))
        for p in self.parts:
            self.assertEqual(p["recipe"], "LWTDismantle" + p["name"])
            self.assertIn(p["recipe"], self.recipes, p["item"])

    def test_the_recipe_is_the_table(self):
        for p in self.parts:
            r = self.recipes[p["recipe"]]
            tool = self.d.TOOLS[p["tool"]]
            self.assertEqual(sorted(r["outputs"]), sorted((n, it) for it, n in p["returns"]),
                             p["recipe"])
            kept = [i for i in r["inputs"] if i[3]]
            used = [i for i in r["inputs"] if not i[3]]
            self.assertEqual([(1, None, lua_list(tool.tags), True)], kept, p["recipe"])
            self.assertEqual([(1, [p["item"]])], [(n, items) for n, items, _, _ in used], p["recipe"])
            self.assertEqual(r["fields"]["category"].strip(), tool.category, p["recipe"])
            self.assertEqual(r["fields"]["timedAction"].strip(), tool.timedAction, p["recipe"])
            self.assertEqual(int(r["fields"]["time"]), p["time"], p["recipe"])

    def test_the_tools_follow_d03(self):
        tools = {p["name"]: p["tool"] for p in self.parts}
        for name in ("Pipe", "Valve", "FlowMeter", "HouseInlet", "BarrelFitting", "Sprinkler"):
            self.assertEqual(tools[name], "plumbing", name)
        for name in ("PondPump", "SprinklerAuto"):
            self.assertEqual(tools[name], "electrical", name)
        for name in ("DripLine", "WaterFilter", "WaterFilterSpent"):
            self.assertEqual(tools[name], "knife", name)
        self.assertEqual(self.d.TOOLS.plumbing.perk, "Maintenance")
        self.assertEqual(self.d.TOOLS.electrical.perk, "Electricity")
        self.assertIsNone(self.d.TOOLS.knife.perk)

    def test_a_dismantle_never_gives_back_more_than_the_build_cost(self):
        for p in self.parts:
            cost = build_cost(p["item"], self.recipes)
            spent, back = defaultdict(float), defaultdict(float)
            for item, n in cost.items():
                fam, w = family(item)
                if fam:
                    spent[fam] += float(n) * w
            for item, n in p["returns"]:
                self.assertGreater(n, 0, p["name"])
                if item in cost:
                    self.assertLessEqual(n, cost[item], "%s gives %d %s" % (p["name"], n, item))
                if item in JUNK:
                    continue
                fam, w = family(item)
                self.assertIsNotNone(fam, "%s gives %s, not a known material" % (p["name"], item))
                back[fam] += n * w
            for fam, w in back.items():
                self.assertLessEqual(w, spent[fam] + 1e-9, "%s gives back more %s than it cost" % (p["name"], fam))

    def test_no_part_gives_back_a_whole_raw_material_it_holds_a_fraction_of(self):
        for p in self.parts:
            cost = build_cost(p["item"], self.recipes)
            for item, _ in p["returns"]:
                self.assertFalse(item in cost and cost[item] < 1, "%s gives a whole %s" % (p["name"], item))
        returns = {p["name"]: {it for it, _ in p["returns"]} for p in self.parts}
        self.assertFalse(returns["Pipe"] & RAW)
        self.assertFalse(returns["DripLine"] & RAW)

    def test_the_water_filter_gives_back_cloth_only(self):
        for item in ("LiveWater.WaterFilter", "LiveWater.WaterFilterSpent"):
            filt = [p for p in self.parts if p["item"] == item][0]
            self.assertEqual(filt["returns"], [("Base.RippedSheets", 1)], item)

    def test_the_recipe_names_are_translated(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in os.listdir(tr):
            with open(os.path.join(tr, lang, "Recipes.json"), encoding="utf-8") as f:
                strings = json.load(f)
            for p in self.parts:
                self.assertTrue(strings.get(p["recipe"]), "%s %s" % (lang, p["recipe"]))


GAME_STUB = r"""
SCRAP_DEFS, SCRAP_ITEMS = {}, {}
Perks = { Maintenance = "perk:Maintenance", Electricity = "perk:Electricity" }
local defs = {}
function defs.addScrapDefinition(material, tools, tools2, perk, time, sound, isWav, baseChance)
    SCRAP_DEFS[material] = { tools = tools, tools2 = tools2, perk = perk, time = time, sound = sound, isWav = isWav,
                             baseChance = baseChance }
    SCRAP_ITEMS[material] = {}
end
function defs.addScrapItem(material, item, maxAmount, chance, isStatic)
    table.insert(SCRAP_ITEMS[material], { item = item, maxAmount = maxAmount, chance = chance, isStatic = isStatic })
end
ISMoveableDefinitions = { getInstance = function() return defs end }
"""


def game_amount(max_amount, size):
    """Items a scrap roll loop gives at full chance: ISMoveableSpriteProps:addScrapItemToList (42.22, ~l.3352)."""
    amount = max_amount
    if size == "Small":
        amount = amount / 2 if amount / 2 >= 1 else 1
    elif size == "Large":
        amount = amount * 2
    return int(amount)  # `for i = 1, amount` runs floor(amount) times


class DismantleInWorld(unittest.TestCase):
    def setUp(self):
        self.lua = new_lua()
        self.lua.execute(GAME_STUB)
        self.lua.execute('require("LiveWater/LWT_GameScrap")')
        self.lua.execute('fire("OnGameBoot")')
        _, self.parts = table(self.lua)
        self.defs = self.lua.globals().SCRAP_DEFS
        self.items = self.lua.globals().SCRAP_ITEMS

    def test_every_placeable_part_but_the_drip_line_has_a_material(self):
        named = {p["name"]: p for p in self.parts}
        for name, size in (("Pipe", "Small"), ("Valve", "Small"), ("FlowMeter", "Small"), ("BarrelFitting", "Small"),
                           ("Sprinkler", "Small"), ("HouseInlet", "Medium"), ("SprinklerAuto", "Medium"),
                           ("PondPump", "Large")):
            self.assertEqual(named[name]["material"], "LiveWater" + name)
            self.assertEqual(named[name]["scrap"], size, name)
            self.assertIsNotNone(self.defs[named[name]["material"]], name)
        for name in ("DripLine", "WaterFilter", "WaterFilterSpent"):
            self.assertIsNone(named[name]["material"])
        self.assertEqual(len(list(self.defs.keys())), 8)

    def test_the_material_gives_the_recipe_outputs_at_full_chance(self):
        d = self.lua.eval('require("LiveWater/LWT_Dismantle")')
        for p in self.parts:
            if p["material"] is None:
                continue
            got = self.items[p["material"]]
            given = {}
            for i in range(1, len(got) + 1):
                e = got[i]
                self.assertTrue(e.isStatic, p["name"])
                self.assertEqual(e.chance, 100, p["name"])
                given[e.item] = game_amount(e.maxAmount, p["scrap"])
            self.assertEqual(given, dict(p["returns"]), p["name"])
            tool = d.TOOLS[p["tool"]]
            df = self.defs[p["material"]]
            self.assertEqual(lua_list(df.tools), lua_list(tool["items"]), p["name"])
            self.assertEqual(len(df.tools2), 0)
            self.assertEqual(df.perk, "perk:" + tool.perk)
            self.assertEqual(df.time, tool.scrapTime)
            self.assertEqual(df.sound, tool.sound)
            self.assertEqual(df.baseChance, tool.baseChance)
            self.assertTrue(df.isWav)


def tiles_module():
    sys.path.insert(0, os.path.join(ROOT, "source", "tiles"))
    try:
        import build_livewater_tiles
    finally:
        sys.path.pop(0)
    return build_livewater_tiles


class DismantleTiles(unittest.TestCase):
    def test_tile_materials_are_the_lua_materials(self):
        tiles = tiles_module()
        _, parts = table(new_lua(DISMANTLE))
        by_item = {p["item"]: p for p in parts}
        seen = set()
        for i in range(tiles.TOTAL):
            props = tiles.tile_props(i)
            item = props.get("CustomItem")
            if item is None:
                continue
            p = by_item[item]
            if p["material"] is None:
                self.assertNotIn("CanScrap", props, i)
            else:
                seen.add(item)
                self.assertIn("CanScrap", props, i)
                self.assertEqual(props["Material"], p["material"], i)
                self.assertEqual(props["ScrapSize"], p["scrap"], i)
        self.assertEqual(seen, {p["item"] for p in parts if p["material"]})


if __name__ == "__main__":
    unittest.main()
