"""Every script item of the mod has its display name in every language (ADR-008 D02)."""
import json
import re
import unittest
from pathlib import Path

MEDIA = Path(__file__).resolve().parents[1] / "Contents" / "mods" / "batman_LiveWater" / "42.21" / "media"
TRANSLATE = MEDIA / "lua" / "shared" / "Translate"


def script_items():
    """Full types ("Module.Name") of the items declared in media/scripts."""
    found = []
    for path in sorted((MEDIA / "scripts").glob("*.txt")):
        module = None
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*module\s+(\w+)", line)
            if m:
                module = m.group(1)
            m = re.match(r"\s*item\s+([A-Za-z_]\w*)\s*$", line)
            if m and module:
                found.append(module + "." + m.group(1))
    return found


class ItemNames(unittest.TestCase):
    def test_the_scripts_declare_items(self):
        self.assertIn("Base.Mov_LiveWater_BarrelFitting", script_items())
        self.assertIn("LiveWater.WaterFilter", script_items())

    def test_every_item_is_named_in_every_language(self):
        items = script_items()
        languages = sorted(p for p in TRANSLATE.iterdir() if p.is_dir())
        self.assertEqual(len(languages), 11)
        for lang in languages:
            names = json.loads((lang / "ItemName.json").read_text(encoding="utf-8"))
            for item in items:
                with self.subTest(language=lang.name, item=item):
                    self.assertTrue(names.get(item, "").strip())


def script_blocks(kind):
    """(name, body) of each block `kind` (item, craftRecipe) of media/scripts."""
    out = []
    for path in sorted((MEDIA / "scripts").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"^\s*" + kind + r"\s+(\w+)\s*\{(.*?)^\s*\}", text, re.S | re.M):
            out.append((m.group(1), m.group(2)))
    return out


class Recipes(unittest.TestCase):
    """ADR-008 D12: every recipe in the crafting panel only, in the category LiveWater."""

    def test_every_recipe_is_in_the_panel_only_and_in_the_category_livewater(self):
        recipes = script_blocks("craftRecipe")
        self.assertGreaterEqual(len(recipes), 20)
        for name, body in recipes:
            with self.subTest(recipe=name):
                self.assertRegex(body, r"category\s*=\s*LiveWater\s*,")
                self.assertNotIn("InHandCraft", body)
                self.assertIn("AnySurfaceCraft", body)

    def test_the_category_is_named_in_every_language(self):
        for lang in sorted(p for p in TRANSLATE.iterdir() if p.is_dir()):
            names = json.loads((lang / "IG_UI.json").read_text(encoding="utf-8"))
            with self.subTest(language=lang.name):
                self.assertEqual(names.get("IGUI_CraftingCategories_LiveWater"), "LiveWater")


class Icons(unittest.TestCase):
    """ADR-008 D12: every item has its own icon file (no default icon, no question mark in the panel)."""

    def test_every_item_has_an_icon_file(self):
        for name, body in script_blocks("item"):
            with self.subTest(item=name):
                m = re.search(r"Icon\s*=\s*(\w+)\s*,", body)
                self.assertIsNotNone(m)
                self.assertNotEqual(m.group(1), "default")
                self.assertTrue((MEDIA / "textures" / ("Item_" + m.group(1) + ".png")).is_file(), m.group(1))


if __name__ == "__main__":
    unittest.main()
