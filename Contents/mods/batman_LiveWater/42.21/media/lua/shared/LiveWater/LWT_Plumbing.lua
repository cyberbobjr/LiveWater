-- LiveWater: plumbing a fixture where the game does not offer it, and taking its plumbing away
-- (ADR-024). Pure rules shared by the client menus and the server command.
-- The game offers "Plumb" only for a fixture in a room (ISWorldObjectContextMenuLogic, Java 42.22:
-- isInARoom and a tank found above); the action itself (ISPlumbItem) and the water of a plumbed
-- fixture (IsoObject.FindExternalWaterSource) need no room.
-- info = { plumbed (uses an outside source), source (a tank stands above it), room (its square is
-- in a room: a room of the map or one the players built), roomBelow (the square under it is) },
-- from LWT_WaterObjects.plumbInfo; nil when there is no fixture.

local Plumbing = {}

-- On a roof (D02): outside any room, right above a room. Not the garden, not bare ground.
function Plumbing.onRoof(info)
    return not info.room and info.roomBelow == true
end

-- Does LiveWater offer the game's "Plumb" for this fixture (D01)? Never where the game does.
function Plumbing.plumbOffer(info)
    return info ~= nil and not info.plumbed and info.source == true and Plumbing.onRoof(info)
end

-- nil when the plumbing of the fixture may be taken away (D04), else the reason: "not_plumbed".
function Plumbing.unplumbRefusal(info)
    if info == nil or not info.plumbed then return "not_plumbed" end
    return nil
end

return Plumbing
