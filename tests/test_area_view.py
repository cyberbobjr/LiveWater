"""ADR-003 D02, D04: right-click a sprinkler or a drip line, one option "Show All Watered Areas" highlights the floor
of every square watered around the player (sprinkler: the square of its radius, D01, with the sandbox multiplier; drip
line: the squares beside it it is not linked to, ADR-004 D02), in one colour; "Hide the Watered Area" clears it."""
import unittest

from lwt_harness import new_lua

FILES = ("shared/LiveWater/LWT_API.lua", "shared/LiveWater/Parts/LWT_PartSprinkler.lua",
         "shared/LiveWater/Parts/LWT_PartPipe.lua", "shared/LiveWater/Parts/LWT_PartDripLine.lua",
         "client/LiveWater/LWT_AreaView.lua")

SETUP = r"""
function getText(key) return key end
PLAYER = { getX = function() return 0.5 end, getY = function() return 0.5 end, getZ = function() return 0 end }
function getSpecificPlayer() return PLAYER end
RADIUS_SCALE = nil
function getSandboxOptions() return { getOptionByName = function(_, name)
    if name == "LiveWater.SprinklerRadiusMultiplier" and RADIUS_SCALE then
        return { getValue = function() return RADIUS_SCALE end } end
    return nil end } end
SQUARES = {}
local function object(sprite)
    local o = { sprite = sprite }
    function o:getSpriteName() return self.sprite end
    function o:getModData() return {} end
    function o:hasModData() return false end
    function o:setHighlightColor(r, g, b, a) self.colour = { r, g, b } end
    function o:setHighlighted(on) self.lit = on end
    return o
end
function square(x, y, sprite)
    local sq = { x = x, y = y, floor = object("floors_01_0"), objs = {} }
    if sprite then table.insert(sq.objs, object(sprite)) end
    function sq:getX() return self.x end
    function sq:getY() return self.y end
    function sq:getZ() return 0 end
    function sq:getFloor() return self.floor end
    function sq:getObjects()
        local l = self.objs
        return { size = function() return #l end, get = function(_, i) return l[i + 1] end }
    end
    SQUARES[x .. "," .. y] = sq
    return sq
end
for x = -12, 12 do for y = -12, 12 do square(x, y) end end
CELL = { getGridSquare = function(_, x, y, z) return SQUARES[x .. "," .. y] end }
function getCell() return CELL end
function menu(sq)
    OPTIONS = {}
    local context = { addOption = function(self, text, target, fn, ...)
        local o = { text = text, run = function(...) fn(target, ...) end, args = { ... } }
        table.insert(OPTIONS, o) return o end }
    fire("OnFillWorldObjectContextMenu", 0, context, { { getSquare = function() return sq end } }, false)
end
function lit()
    local n = 0
    for _, sq in pairs(SQUARES) do if sq.floor.lit then n = n + 1 end end
    return n
end
function option(text)
    for _, o in ipairs(OPTIONS) do if o.text == text then return o end end
    return nil
end
"""


class AreaView(unittest.TestCase):
    def lua(self):
        lua = new_lua(*FILES)
        lua.execute(SETUP)
        lua.execute('SPR = square(0, 0, "batman_livewater_01_48")')
        return lua

    def show_all(self, lua, sq):
        lua.execute("menu(%s) local o = option('ContextMenu_LWT_ShowAllAreas') o.run(unpack(o.args))" % sq)

    def test_one_option_on_a_sprinkler_lights_its_25_squares_and_hide_clears_them(self):
        lua = self.lua()
        lua.execute("menu(SPR)")
        self.assertEqual(len([o for o in lua.eval("OPTIONS").values()]), 1)
        self.show_all(lua, "SPR")
        self.assertEqual(lua.eval("lit()"), 25)
        self.assertTrue(lua.eval("SQUARES['2,2'].floor.lit"))
        self.assertFalse(bool(lua.eval("SQUARES['3,0'].floor.lit")))
        lua.execute("menu(SPR)")
        self.assertIsNone(lua.eval('option("ContextMenu_LWT_ShowAllAreas")'))
        lua.execute('local o = option("ContextMenu_LWT_HideArea") o.run(unpack(o.args))')
        self.assertEqual(lua.eval("lit()"), 0)

    def test_the_sandbox_multiplier_widens_the_area(self):
        lua = self.lua()
        lua.execute("RADIUS_SCALE = 1.5")
        self.show_all(lua, "SPR")
        self.assertEqual(lua.eval("lit()"), 49)

    def test_a_straight_drip_line_waters_the_squares_on_each_side(self):
        lua = self.lua()
        lua.execute('SPR.objs = {} D = square(8, 0, "batman_livewater_01_170")')
        self.show_all(lua, "D")
        self.assertEqual(lua.eval("lit()"), 2)
        self.assertTrue(lua.eval("SQUARES['8,-1'].floor.lit and SQUARES['8,1'].floor.lit"))

    def test_sprinklers_and_drip_lines_around_are_lit_in_one_colour(self):
        lua = self.lua()
        lua.execute('D = square(8, 0, "batman_livewater_01_170")')
        self.show_all(lua, "D")
        self.assertEqual(lua.eval("lit()"), 27)
        spray = lua.eval("SQUARES['1,1'].floor.colour")
        drip = lua.eval("SQUARES['8,1'].floor.colour")
        self.assertEqual(tuple(spray.values()), tuple(drip.values()))

    def test_offered_only_on_a_part_that_waters(self):
        lua = self.lua()
        lua.execute('P = square(9, 9, "batman_livewater_01_10") menu(P)')
        self.assertIsNone(lua.eval('option("ContextMenu_LWT_ShowAllAreas")'))
        lua.execute("menu(SQUARES['3,3'])")
        self.assertIsNone(lua.eval('option("ContextMenu_LWT_ShowAllAreas")'))

if __name__ == "__main__":
    unittest.main()
