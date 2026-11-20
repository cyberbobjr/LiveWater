if isClient() then return end
-- LiveWater: water as soon as a fixture is plumbed (ADR-018 D01, D02), on the authority.
-- Plumbing a sink, bathtub, shower, toilet or washing machine with the wrench (vanilla ISPlumbItem)
-- adds no object, so no OnObjectAdded tells LiveWater; the vanilla action is wrapped instead.
--   PlumbWatch.wrap(class, probe, react)  wraps class.complete once (a second call, another game
--       loaded in the same session, does nothing): the original runs first with the same arguments
--       and its results are returned unchanged; probe(action) -> x, y, z of the fixture the action
--       works on when it uses an outside water source, else nil; react(x, y, z) runs only when the
--       fixture did not use one before and does after (the plumbing succeeded). Returns true when
--       it wrapped.
--   PlumbWatch.new(deps):plumbed(x, y, z)  the relays around the square are surveyed again
--       (Relays:touched) and the network of every house inlet whose area covers the square brings
--       one step forward at once (Clock:hasten -> Clock:bringForward, the valves' immediate step,
--       capped by Clock.MAX_AHEAD). Returns the network ids stepped.
-- Where the action runs (Java 42.22): solo, LuaTimedActionNew.complete() calls the Lua complete when
-- not GameClient.client (LuaTimedActionNew.java:161-167); multiplayer, the server rebuilds the action
-- (NetTimedAction.parse, NetTimedAction.java:145-169) and calls its complete (NetTimedAction.perform,
-- NetTimedAction.java:134-136), never the client. ISPlumbItem is a shared file
-- (media/lua/shared/TimedActions/ISPlumbItem.lua, complete() lines 31-43), loaded on a dedicated
-- server too. The function is looked up on the class at call time (KahluaTableImpl.rawget falls back
-- to the metatable), so a wrapper set on the class is the one called.
-- No game API here; dependencies are injected: { relays (touched, covering), clock (hasten) }.

local PlumbWatch = {}
PlumbWatch.__index = PlumbWatch

-- Field of the wrapped class holding the wrapper: present and still in place means already wrapped.
PlumbWatch.MARK = "LiveWaterPlumbWatch"

function PlumbWatch.new(deps)
    return setmetatable({ relays = deps.relays, clock = deps.clock }, PlumbWatch)
end

function PlumbWatch:plumbed(x, y, z)
    self.relays:touched(x, y, z)
    return self.clock:hasten(self.relays:covering(x, y, z))
end

function PlumbWatch.wrap(class, probe, react)
    if not class or type(class.complete) ~= "function" then return false end
    if class[PlumbWatch.MARK] ~= nil and class.complete == class[PlumbWatch.MARK] then return false end
    local original = class.complete
    local function finish(before, action, ...)
        if before == nil then
            local x, y, z = probe(action)
            if x ~= nil then react(x, y, z) end
        end
        return ...
    end
    local function complete(action, ...)
        local before = probe(action)
        return finish(before, action, original(action, ...))
    end
    class.complete = complete
    class[PlumbWatch.MARK] = complete
    return true
end

return PlumbWatch
