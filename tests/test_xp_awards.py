"""ADR-015: experience given by every LiveWater recipe (Metalworking for metal parts, Electrical for the pump).

Reads the recipe scripts; the engine side (xpAward of a craftRecipe) is vanilla.
Run: python -B tests/test_xp_awards.py
"""
import re
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "Contents/mods/batman_LiveWater/42.21/media/scripts"

EXPECTED = {
    # making (D01)
    "LWTCutPipeSections": "MetalWelding:5",
    "LWTBuildValve": "MetalWelding:5",
    "LWTBuildBarrelFitting": "MetalWelding:5",
    "LWTBuildFlowMeter": "MetalWelding:8",
    "LWTBuildSprinkler": "MetalWelding:8",
    "LWTBuildHouseInlet": "MetalWelding:10",
    "LWTBuildPondPump": "Electricity:15",
    "LWTUpgradeSprinkler": "Electricity:10",
    # dismantling (D02)
    "LWTDismantlePipe": "MetalWelding:2",
    "LWTDismantleValve": "MetalWelding:2",
    "LWTDismantleFlowMeter": "MetalWelding:2",
    "LWTDismantleHouseInlet": "MetalWelding:2",
    "LWTDismantleSprinkler": "MetalWelding:2",
    "LWTDismantleBarrelFitting": "MetalWelding:2",
    "LWTDismantlePondPump": "Electricity:5",
    "LWTDismantleSprinklerAuto": "Electricity:3",
    # neither metal nor electrical (D03)
    "LWTMakeWaterFilter": None,
    "LWTRechargeWaterFilter": None,
    "LWTMakeDripLine": None,
    "LWTDismantleWaterFilter": None,
    "LWTDismantleWaterFilterSpent": None,
    "LWTDismantleDripLine": None,
}

# Required levels stay as they were (D04).
REQUIRED = {"LWTBuildPondPump": "Electricity:2", "LWTUpgradeSprinkler": "Electricity:2"}


def recipes():
    out = {}
    for path in sorted(SCRIPTS.glob("LWT_*.txt")):
        text = path.read_text(encoding="ascii")
        for match in re.finditer(r"craftRecipe\s+(\w+)\s*\{", text):
            level, end = 1, match.end()
            while level:
                level += (text[end] == "{") - (text[end] == "}")
                end += 1
            out[match.group(1)] = text[match.end():end]
    return out


class XpAwards(unittest.TestCase):
    def test_every_recipe_is_classified(self):
        self.assertEqual(set(recipes()), set(EXPECTED))

    def test_awards(self):
        for name, body in recipes().items():
            awards = re.findall(r"xpAward\s*=\s*([\w:]+)\s*,", body)
            with self.subTest(recipe=name):
                self.assertEqual(awards, [EXPECTED[name]] if EXPECTED[name] else [])

    def test_required_levels_unchanged(self):
        for name, body in recipes().items():
            with self.subTest(recipe=name):
                self.assertEqual(re.findall(r"SkillRequired\s*=\s*([\w:]+)\s*,", body),
                                 [REQUIRED[name]] if name in REQUIRED else [])


if __name__ == "__main__":
    unittest.main()
