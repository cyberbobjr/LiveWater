-- LiveWater: game adapter of the sandbox multipliers (page LiveWater, ADR-001 D07), shared: the
-- client reads the same options (watered area, ADR-003 D02; sandbox options reach MP clients). Read on every
-- call through getSandboxOptions (SandboxVars may be stale in solo after the in-game editor).

local GameSettings = {}

-- function(name) -> value of the option "LiveWater.<name>", or nil when it does not exist.
function GameSettings.scale(name)
    local option = getSandboxOptions():getOptionByName("LiveWater." .. name)
    return option and option:getValue() or nil
end

return GameSettings
