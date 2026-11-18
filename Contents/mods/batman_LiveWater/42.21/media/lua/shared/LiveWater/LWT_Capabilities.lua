-- LiveWater: registry of capability kinds (ADR-001 D02). A capability is a strategy: a table
-- of hook functions, copied by whitelist at registration. Every hook takes the checked
-- params of the part definition first. Hooks:
--   define(params)  required: whitelist copy of the params with their defaults, or nil and
--                   the name of the invalid field (params is {} when the part wrote `true`).
-- Optional hooks take (params, data), data being the part's own state for this kind
-- (part.data[kind], possibly nil, ADR-001 D04):
--   carries(p, d)      water goes through the part (network)
--   blocks(p, d)       the part cuts the water now, e.g. a closed valve (network)
--   pressurizes(p, d)  the part puts its network under pressure: water starts there (network)
--   ports(p, d)        most pipes that may leave the part (network)
--   supply(p, d, ctx)  pressure and litres per ten-minute step the part gives (flow)
--   source(p, d, ctx)  quality of the water the part takes ("clean", "tainted"), nil when dry (flow)
--   outlet(p, d)       pressure cost and "needs clean water" of a part water leaves by (flow)
--   purifies(p, d, ctx) the part makes the water going through it clean now (flow)
--   wear(p, d, litres, ctx) litres went through the part; d is created when absent (flow)
--   layable(p, d)      full type of the item the part is laid with and tag of the tool that
--                      dismantles it (server commands)
-- Revision 2 (pond pump, power):
--   look(p, d)         token of the part's look ("on", "filter"); the tokens of all its
--                      capabilities, joined by "_" in kind order, name the variant drawn
--   attach(p, d, site) may the part stand there? true, or false and a reason; may record what
--                      it found in d (created). site: port of LWT_GameSite (source())
--   power(p, d)        needs current (bool) and watts drawn now
--   powered(p, d, on)  the authority tells whether the part has current this step (d created)
--   stepped(p, d, outcome, ctx)  end of a step: outcome = { through = litres that went through
--                      the part, quality = of that water (revision 5: per part; the network's
--                      water when none went through) } (d created)
--   output(p, d)       litres the part gave the network last step (Live Wire summary)
--   lines(p, d)        text lines { { key, arg, ..., rank = n } } (information, Live Wire)
-- Revision 3 (filter cartridge, part menu):
--   cartridge(p, d, ctx)  removable cartridge: item full type, fitted (bool), share left 0..1
--   fit(p, d, share, ctx) a cartridge with `share` left goes in (d created)
--   unfit(p, d)           the cartridge comes out (d created)
--   actions(p, d)         actions of the part menu: { { command, key, item = item to carry } }
-- Revision 4 (pump upkeep):
--   switchable(p, d)      the part has a switch: its position (true = on), else nil
--   switch(p, d, on)      set the switch (d created)
--   repairable(p, d)      repair: material full type, count, tool tag or nil, and the reason it
--                         cannot be done now ("running", "not_needed") or nil
--   repair(p, d)          the repair is done (d created)
--   sound(p, d)           sound loop name, noise radius and volume while it makes noise, else nil
-- Revision 7 (house inlet): outlet(p, d) also gives the outlet type (third result); the outcome of
--   stepped carries `outlet` = what the step did with an outlet ("served", "idle", "closed",
--   "no_water", "unfiltered", "no_pressure"; nil for a part that is not one).
-- Revision 8 (sprinklers, valves):
--   spray(p, d, ctx)      a part that waters plants: radius (squares) and litres of a dose
--   jet(p, d)             frames of the animated jet the clients draw: sprite prefix, first index,
--                         frame count, and whether it sprays now (D08a)
--   opened(p, d)          a valve: open now (true/false), else nil
--   open(p, d, on)        open or close it (d created)
-- Revision 9 (timers):
--   prepare(p, d, ctx)    start of a step, after `powered`: a timer may hold its part open (d created)
--   opens(p, d)           the part is held open now even if a valve of it is closed (Parts:closed)
--   timer(p, d)           hours between two openings of a timer, else nil
--   setTimer(p, d, hours) a player set them (d created)
--   actions may carry `choices` = { { key, arg, args } }: a submenu, args sent with the command
-- ctx is the context of the step: { need, hours (revision 9: world age in hours), scale = function(optionName) -> multiplier,
-- random = function() -> 0..1 (breakdowns; none without it), sources = registry of source kinds
-- (revision 6, LWT_Sources) }.

local Check = require "LiveWater/LWT_Check"

local HOOKS = { "define", "carries", "blocks", "pressurizes", "ports", "supply", "source", "outlet", "purifies",
    "wear", "layable", "look", "attach", "power", "powered", "stepped", "output", "lines",
    "cartridge", "fit", "unfit", "actions", "switchable", "switch", "repairable", "repair", "sound",
    "spray", "jet", "opened", "open", "prepare", "opens", "timer", "setTimer" }

local Capabilities = {}
Capabilities.__index = Capabilities

function Capabilities.new()
    return setmetatable({ impls = {}, sealed = false }, Capabilities)
end

local function isKind(v)
    return Check.isName(v) or Check.isNamespaced(v)
end

local function copyHooks(impl)
    if type(impl) ~= "table" or type(impl.define) ~= "function" then return nil end
    local out = {}
    for i = 1, #HOOKS do
        local hook = impl[HOOKS[i]]
        if hook ~= nil then
            if type(hook) ~= "function" then return nil end
            out[HOOKS[i]] = hook
        end
    end
    return out
end

-- Returns true, or false and "registration_closed", "invalid_kind", "duplicate_capability",
-- "invalid_implementation".
function Capabilities:register(kind, impl)
    if self.sealed then return false, "registration_closed" end
    if not isKind(kind) then return false, "invalid_kind" end
    if self.impls[kind] then return false, "duplicate_capability" end
    local hooks = copyHooks(impl)
    if not hooks then return false, "invalid_implementation" end
    self.impls[kind] = hooks
    return true
end

function Capabilities:get(kind)
    return self.impls[kind]
end

function Capabilities:seal()
    self.sealed = true
end

return Capabilities
