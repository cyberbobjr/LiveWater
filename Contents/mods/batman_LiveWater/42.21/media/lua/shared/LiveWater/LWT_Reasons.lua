-- LiveWater: refusal reason -> translation key told to the player (IG_UI.json). Shared by the
-- server commands (note above the player) and the furniture cursor rule (info panel line).

local Reasons = {
    KEYS = {
        invalid = "IGUI_LWT_Invalid",
        not_layable = "IGUI_LWT_NotLayable",
        too_far = "IGUI_LWT_TooFar",
        not_loaded = "IGUI_LWT_TooFar",
        blocked = "IGUI_LWT_Blocked",
        occupied = "IGUI_LWT_Occupied",
        ports_full = "IGUI_LWT_PortsFull",
        no_item = "IGUI_LWT_NoItem",
        need_tool = "IGUI_LWT_NeedTool",
        nothing_here = "IGUI_LWT_NothingHere",
        no_source = "IGUI_LWT_NoSource",
        no_cartridge = "IGUI_LWT_NoFilter",
        no_filter = "IGUI_LWT_NoFilterFitted",
        no_filter_slot = "IGUI_LWT_NoFilterSlot",
        not_switchable = "IGUI_LWT_Invalid",
        not_repairable = "IGUI_LWT_Invalid",
        running = "IGUI_LWT_StillRunning",
        not_needed = "IGUI_LWT_NotNeeded",
        need_wrench = "IGUI_LWT_NeedWrench",
        no_parts = "IGUI_LWT_NoScrap",
        not_barrel = "IGUI_LWT_NotBarrel",
        no_inlet = "IGUI_LWT_NoInlet",
        not_connected = "IGUI_LWT_NotConnected",
        not_fixture = "IGUI_LWT_NotFixture",
        not_map_building = "IGUI_LWT_NotMapBuilding",
        no_city_water = "IGUI_LWT_NoCityWater",
        not_valve = "IGUI_LWT_Invalid",
        not_timer = "IGUI_LWT_Invalid",
        out_of_bounds = "IGUI_LWT_OutOfBounds",
        not_fitting = "IGUI_LWT_Invalid",
    },
    GENERIC = "IGUI_LWT_Refused",
}

-- Translation key of a reason.
function Reasons.key(reason)
    return Reasons.KEYS[reason] or Reasons.GENERIC
end

return Reasons
