if isClient() then return end
-- LiveWater command "showNetwork" { x, y, z }: the squares of the network of the part there go back to
-- the player (reply "network" { parts = { { x, y, z } }, fixtures = { { x, y, z, status } } }), who
-- highlights them (LWT_NetworkView, D11). The fixtures are those of the area of each house inlet of
-- the network, with how they get water (LWT_Relays.fixtureStates, ADR-008 D06), each once.
-- Checks: arguments, a part on the square, distance. At most MAX_PARTS squares and MAX_FIXTURES
-- fixtures.

local Checks = require "LiveWater/Commands/LWT_CmdChecks"
local Grid = require "LiveWater/LWT_Grid"
local Protocol = require "LiveWater/LWT_Protocol"

local MAX_PARTS = 500
local MAX_FIXTURES = 300

-- Fixtures of the inlets among the members, each square once.
local function fixturesOf(relays, members)
    local out, seen = {}, {}
    if not relays then return out end
    for i = 1, #members do
        if relays:isInlet(members[i]) then
            local list = relays:fixtureStates(members[i])
            for j = 1, #list do
                local f = list[j]
                local key = Grid.key(f.x, f.y, f.z)
                if not seen[key] and #out < MAX_FIXTURES then
                    seen[key] = true
                    out[#out + 1] = { x = f.x, y = f.y, z = f.z, status = f.status }
                end
            end
        end
    end
    return out
end

return function(ctx, player, args)
    local x, y, z = Checks.square(args)
    if not x then return false, "invalid" end
    if not ctx.topology:at(x, y, z) then return false, "nothing_here" end
    if not Checks.near(ctx.players, player, x, y, z) then return false, "too_far" end
    local members, parts = ctx.topology:networkOf(x, y, z), {}
    for i = 1, math.min(#members, MAX_PARTS) do
        parts[i] = { x = members[i].x, y = members[i].y, z = members[i].z }
    end
    ctx.replies:to(player, Protocol.NETWORK, { parts = parts, fixtures = fixturesOf(ctx.relays, members) })
    return true
end
