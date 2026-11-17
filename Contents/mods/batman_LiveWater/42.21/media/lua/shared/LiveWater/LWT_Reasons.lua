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
    },
    GENERIC = "IGUI_LWT_Refused",
}

-- Translation key of a reason.
function Reasons.key(reason)
    return Reasons.KEYS[reason] or Reasons.GENERIC
end

return Reasons
