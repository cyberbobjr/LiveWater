"""Debug-only submenu that gives the test kit: every LiveWater item of the scripts, 20 pipe sections, 20 drip lines and a
pipe wrench; added to the inventory in solo, asked with /additem on a server; hidden without -debug."""
import glob
import os
import re
import unittest

from lwt_harness import ROOT, new_lua

MEDIA = os.path.join(ROOT, "Contents", "mods", "batman_LiveWater", "42.21", "media")


def script_items():
    """Full names of the items the mod's scripts declare."""
    names = []
    for path in glob.glob(os.path.join(MEDIA, "scripts", "*.txt")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        module = re.search(r"^module\s+(\w+)", text, re.M).group(1)
        names += ["%s.%s" % (module, n) for n in re.findall(r"^\s*item\s+(\w+)\s*$", text, re.M)]
    return names


SETUP = r"""
DEBUG, CLIENT = false, false
function isDebugEnabled() return DEBUG end
function isClient() return CLIENT end
function getText(key) return key end
ADDED, SENT = {}, {}
PLAYER = {
    getUsername = function() return "Tester" end,
    getInventory = function() return { AddItem = function(self, name) ADDED[name] = (ADDED[name] or 0) + 1 end } end,
}
function getSpecificPlayer() return PLAYER end
function SendCommandToServer(text) table.insert(SENT, text) end
local function item(name) return { getFullName = function() return name end } end
local list = { item("Base.Axe"), item("Base.Mov_FridgeOld") }
for i = 1, #NAMES do list[#list + 1] = item(NAMES[i]) end
function getAllItems() return { size = function() return #list end, get = function(self, i) return list[i + 1] end } end
function newMenu()
    local m = { options = {}, subs = {} }
    function m:addOption(text, target, fn, ...)
        local o = { text = text, target = target, fn = fn }
        table.insert(self.options, o)
        return o
    end
    function m:addSubMenu(option, sub) option.sub = sub end
    return m
end
ISContextMenu = { getNew = function(self, parent) return newMenu() end }
function menu()
    ROOT = newMenu()
    fire("OnFillWorldObjectContextMenu", 0, ROOT, {}, false)
end
function give() local o = ROOT.options[1].sub.options[1] o.fn(o.target) end
"""


class DebugKit(unittest.TestCase):
    def setUp(self):
        self.names = script_items()
        self.lua = new_lua("client/LiveWater/LWT_DebugMenu.lua")
        self.lua.execute("NAMES = {%s}" % ",".join('"%s"' % n for n in self.names))
        self.lua.execute(SETUP)

    def test_hidden_without_debug(self):
        self.lua.execute("menu()")
        self.assertEqual(self.lua.eval("#ROOT.options"), 0)

    def test_solo_gives_every_item_twenty_pipes_twenty_drip_lines_and_a_pipe_wrench(self):
        self.lua.execute("DEBUG = true menu()")
        self.assertEqual(self.lua.eval("ROOT.options[1].text"), "ContextMenu_LWT_Debug")
        self.assertEqual(self.lua.eval("ROOT.options[1].sub.options[1].text"), "ContextMenu_LWT_DebugKit")
        self.lua.execute("give()")
        added = dict(self.lua.eval("ADDED").items())
        expected = {n: 1 for n in self.names}
        expected["Base.Mov_LiveWater_Pipe"] = 20
        expected["Base.Mov_LiveWater_DripLine"] = 20
        expected["Base.PipeWrench"] = 1
        self.assertEqual(added, expected)
        self.assertTrue(any(n.startswith("Base.Mov_LiveWater_") for n in added))

    def test_server_asks_additem_with_counts(self):
        self.lua.execute("DEBUG, CLIENT = true, true menu() give()")
        sent = list(self.lua.eval("SENT").values())
        self.assertIn('/additem "Tester" "Base.Mov_LiveWater_Pipe" 20', sent)
        self.assertIn('/additem "Tester" "Base.Mov_LiveWater_DripLine" 20', sent)
        self.assertIn('/additem "Tester" "Base.PipeWrench" 1', sent)
        self.assertEqual(len(sent), len(self.names) + 1)
        self.assertEqual(self.lua.eval("next(ADDED)"), None)


if __name__ == "__main__":
    unittest.main()
