--[[
Hooks of pzdev for LiveWater, mode `server` (dedicated server alone, no player): the server files load and the
authority is built (LiveWater.Server with its services and command handlers), part types registered, no Lua
error. ASCII only (Kahlua lexer).
]]

local H = { server = {} }

local lines, ok = {}, true

local function rec(pass, name, detail)
    if not pass then ok = false end
    lines[#lines + 1] = (pass and "PASS " or "FAIL ") .. name .. (detail ~= nil and (" - " .. tostring(detail)) or "")
end

function H.server.start(ctx)
    lines, ok = {}, true
    local s = LiveWater and LiveWater.Server
    rec(s ~= nil, "LiveWater authority built on the dedicated server")
    local ids = LiveWater and LiveWater.Parts and LiveWater.Parts:ids() or {}
    rec(#ids >= 7, "part types registered", tostring(#ids) .. ": " .. table.concat(ids, ", "))
    local handlers = 0
    if s then
        for _ in pairs(s.commands.handlers) do handlers = handlers + 1 end
    end
    rec(handlers >= 15, "command handlers registered", tostring(handlers))
    rec(s ~= nil and s.clock ~= nil and s.relays ~= nil, "clock and relay services present")
    local n = getLuaDebuggerErrorCount and getLuaDebuggerErrorCount() or 0
    rec(n == 0, "no Lua error recorded", "errors=" .. tostring(n))
    return true
end

function H.server.result(ctx)
    local pass, total = 0, 0
    for i = 1, #lines do
        if lines[i]:sub(1, 4) == "PASS" then pass = pass + 1 end
        total = total + 1
    end
    return { ok = ok and total > 0, summary = pass .. "/" .. total .. " PASS", lines = lines }
end

return H
