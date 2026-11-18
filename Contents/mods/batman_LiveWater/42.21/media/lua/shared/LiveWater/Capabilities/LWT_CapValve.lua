-- LiveWater capability "valve": open or closed; closed, it cuts everything after it (D02).
--   open  state of a newly placed part (default true)
-- State: { open = set by a player (nil: as placed) }.
-- Revision 8: hooks opened (position), open (set it: command switchValve), actions, lines.

local Check = require "LiveWater/LWT_Check"

local SPEC = { open = Check.boolean(true) }

local Valve = {}

function Valve.define(params)
    return Check.fields(params, SPEC)
end

-- Open now: its state, else as placed.
function Valve.opened(p, d)
    if d and d.open ~= nil then return d.open end
    return p.open
end

function Valve.open(p, d, on)
    d.open = on == true
end

function Valve.blocks(p, d)
    return not Valve.opened(p, d)
end

function Valve.actions(p, d)
    if Valve.opened(p, d) then return { { command = "switchValve", key = "ContextMenu_LWT_CloseValve" } } end
    return { { command = "switchValve", key = "ContextMenu_LWT_OpenValve" } }
end

function Valve.lines(p, d)
    return { { Valve.opened(p, d) and "IGUI_LWT_Valve_Open" or "IGUI_LWT_Valve_Closed", rank = 5 } }
end

return Valve
