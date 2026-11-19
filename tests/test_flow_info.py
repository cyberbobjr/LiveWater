"""ADR-006 D09: the player reads the watering flow in the "Information" of a sprinkler and of a drip line: litres per
ten minutes (sandbox SprinklerFlow / DripFlow or the part's own `flow`), and for a sprinkler the litres that reach the
plants (a quarter is lost in the air); the lines hooks get the sandbox context (Parts:lines(part, ctx))."""
import json
import os
import unittest

from lwt_harness import ROOT, new_lua

API = "shared/LiveWater/LWT_API.lua"
PARTS = ("shared/LiveWater/Parts/LWT_PartSprinkler.lua", "shared/LiveWater/Parts/LWT_PartDripLine.lua")
MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")


def lines(lua, part_type, scale="{}"):
    lua.execute("SCALE = %s" % scale)
    t = lua.eval('LiveWater.Parts:lines({ type = "%s", data = {} }, { scale = function(n) return SCALE[n] end })'
                 % part_type)
    out = []
    for i in range(1, len(t) + 1):
        line = t[i]
        out.append(tuple(line[j] for j in range(1, len(line) + 1)))
    return out


class FlowLines(unittest.TestCase):
    def lua(self):
        return new_lua(API, *PARTS)

    def test_a_sprinkler_tells_its_flow_and_what_reaches_the_plants(self):
        self.assertIn(("IGUI_LWT_Flow_Spray", "10", "7.5"), lines(self.lua(), "LiveWater:Sprinkler"))

    def test_the_sandbox_flow_is_shown(self):
        self.assertIn(("IGUI_LWT_Flow_Spray", "4", "3"),
                      lines(self.lua(), "LiveWater:Sprinkler", "{ SprinklerFlow = 4 }"))

    def test_a_drip_line_tells_its_flow_per_square(self):
        lua = self.lua()
        self.assertIn(("IGUI_LWT_Flow_Drip", "0.5"), lines(lua, "LiveWater:DripLine"))
        self.assertIn(("IGUI_LWT_Flow_Drip", "0.2"), lines(lua, "LiveWater:DripLine", "{ DripFlow = 0.2 }"))

    def test_the_lines_are_translated_with_their_arguments(self):
        tr = os.path.join(MEDIA, "lua", "shared", "Translate")
        for lang in os.listdir(tr):
            with open(os.path.join(tr, lang, "IG_UI.json"), encoding="utf-8") as f:
                strings = json.load(f)
            self.assertIn("%2", strings["IGUI_LWT_Flow_Spray"], lang)
            self.assertIn("%1", strings["IGUI_LWT_Flow_Drip"], lang)


if __name__ == "__main__":
    unittest.main()
