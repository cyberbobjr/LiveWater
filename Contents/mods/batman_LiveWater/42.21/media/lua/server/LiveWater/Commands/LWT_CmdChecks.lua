if isClient() then return end
-- LiveWater: argument and reach checks shared by the command handlers (LiveWater/Commands).

local Checks = {}

-- Chebyshev distance on the player's floor within which a player may act on a square.
Checks.RANGE = 3

-- Tag of the pipe wrench (Java 42.22 ItemTag.PIPE_WRENCH): plumbing actions.
Checks.PIPE_WRENCH = "base:pipewrench"

local function isCoordinate(v)
    return type(v) == "number" and v == v and v % 1 == 0 and v >= -1000000 and v <= 1000000
end

-- x, y, z of the args when they are integers, else nil.
function Checks.square(args)
    if isCoordinate(args.x) and isCoordinate(args.y) and isCoordinate(args.z) then
        return args.x, args.y, args.z
    end
    return nil
end

-- Is the player on floor z within RANGE of the square? `players` is the players port.
function Checks.near(players, player, x, y, z)
    local px, py, pz = players:position(player)
    if not px or math.floor(pz) ~= z then return false end
    return math.abs(math.floor(px) - x) <= Checks.RANGE and math.abs(math.floor(py) - y) <= Checks.RANGE
end

return Checks
