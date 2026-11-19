"""ADR-007 D04: plumbing parts are found in plumbing supplies and tool crates, watering parts in garden stores and
farming supplies, at low weights, added to the vanilla procedural lists when the tables merge without replacing
anything. The pond pump, the house inlet, the water meter and the automatic sprinkler are never found."""
import os
import re
import unittest

from lwt_harness import ROOT, new_lua

LOOT = "server/LiveWater/LWT_Loot.lua"
SCRIPTS = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media", "scripts")
PLUMBING = ("PlumbingSupplies", "CrateTools", "GarageTools", "ToolStoreTools")
GARDEN = ("GardenStoreTools", "GardenStoreMisc", "CrateGardening", "GigamartFarming", "ToolStoreFarming")
NEVER = {"Base.Mov_LiveWater_PondPump", "Base.Mov_LiveWater_HouseInlet", "Base.Mov_LiveWater_FlowMeter",
         "Base.Mov_LiveWater_SprinklerAuto"}
FOUND = {"Base.Mov_LiveWater_Pipe": PLUMBING, "Base.Mov_LiveWater_Valve": PLUMBING,
         "Base.Mov_LiveWater_BarrelFitting": PLUMBING, "Base.Mov_LiveWater_Sprinkler": GARDEN,
         "Base.Mov_LiveWater_DripLine": GARDEN, "LiveWater.WaterFilter": GARDEN}


def script_items():
    out = set()
    for name, module in (("LWT_moveables.txt", "Base"), ("LWT_items.txt", "LiveWater")):
        with open(os.path.join(SCRIPTS, name), encoding="ascii") as f:
            out |= {"%s.%s" % (module, it) for it in re.findall(r"^\s*item\s+(\w+)", f.read(), re.M)}
    return out


def merged(missing=()):
    """Run the merge on a vanilla-like ProceduralDistributions; return {list: [(item, weight)]} after it."""
    lua = new_lua()
    names = [n for n in PLUMBING + GARDEN + ("KitchenPots",) if n not in missing]
    lua.execute("ProceduralDistributions = { list = {} }")
    for n in names:
        lua.execute('ProceduralDistributions.list.%s = { rolls = 4, items = { "Hammer", 10, "Base.Nails", 0.5 } }' % n)
    lua.execute('require("LiveWater/LWT_Loot")')
    lua.execute('fire("OnPreDistributionMerge")')
    out = {}
    lists = lua.globals().ProceduralDistributions.list
    for n in list(lists.keys()):
        items = lists[n]["items"]
        out[n] = [(items[i], items[i + 1]) for i in range(1, len(items) + 1, 2)]
    return out


class Loot(unittest.TestCase):
    def test_the_vanilla_entries_stay_first_and_untouched(self):
        for n, entries in merged().items():
            self.assertEqual(entries[:2], [("Hammer", 10), ("Base.Nails", 0.5)], n)
        self.assertEqual(merged()["KitchenPots"], [("Hammer", 10), ("Base.Nails", 0.5)])

    def test_each_part_is_found_where_d04_puts_it(self):
        lists = merged()
        for item, where in FOUND.items():
            for n, entries in lists.items():
                added = [w for it, w in entries[2:] if it == item]
                self.assertEqual(len(added), 1 if n in where else 0, "%s in %s" % (item, n))
                for w in added:
                    self.assertTrue(0.5 <= w <= 2, "%s weight %s in %s" % (item, w, n))

    def test_only_real_items_are_added_and_never_the_crafted_only_parts(self):
        known = script_items()
        for n, entries in merged().items():
            for it, _ in entries[2:]:
                self.assertIn(it, known, n)
                self.assertNotIn(it, NEVER, n)

    def test_a_missing_list_is_skipped(self):
        lists = merged(missing=("GarageTools", "GigamartFarming"))
        self.assertNotIn("GarageTools", lists)
        self.assertNotIn("GigamartFarming", lists)
        self.assertIn("Base.Mov_LiveWater_Pipe", [it for it, _ in lists["CrateTools"]])


if __name__ == "__main__":
    unittest.main()
