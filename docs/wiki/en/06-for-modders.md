# For modders: the public API

LiveWater is an **open water network**: its own pipes, pumps, inlets and sprinklers are registered through the same
public API another mod uses. A new part is a data file; a new behaviour is a capability.

## Rules

- Register from a file in `media/lua/shared`, while the game loads, **before `OnInitGlobalModData`**. Afterwards every
  registration is refused with `registration_closed`.
- Every refusal returns `false` and a reason, and writes an English warning in the console. Nothing throws.
- Ids are namespaced: `"<YourMod>:<Name>"`.
- Check `LiveWater.API.revision` before using a function or field added after revision 1.

## Functions

| Function | Role |
|---|---|
| `LiveWater.API.registerPart(id, definition)` | a new part type: `sprites` (`{ [mask] = sprite }`, masks 0-15, redrawn by the connections) or `variants` (sprites chosen by state, 4 facings S, E, N, W), `crossings` (revision 14: `{ [mask] = { [edges] = sprite } }`, edges 1 = N, 8 = W, 9 = both, within the mask: the shape drawn with a sleeve where it crosses a fence carried by its own N or W edge; refused as `invalid_crossings`), `sides` (connectable sides mask, 15 by default), `capabilities` (`{ kind = settings or true }`) |
| `LiveWater.API.registerCapability(kind, implementation)` | a new capability; `implementation.define(params)` is required, every hook is optional |
| `LiveWater.API.part(id)` | a checked copy of a part definition, or `nil` |
| `LiveWater.API.registerSource(kind, definition)` | revision 6: a kind of water source `{ quality = "clean" or "tainted", flag = IsoFlagType of a nearby square, sprites = { nearby object sprites } }` |
| `LiveWater.API.registerContainer(name, definition)` | revision 11: a container a barrel fitting can fill, by sprite or entity name, `{ shape = "tall" or "low" }`; filled like a barrel, with tainted water (ADR-005 D07; the field `clean` of revision 12 is ignored) |
| `LiveWater.Events.on(name, fn)` / `off(name, fn)` | events on the authority: `partAdded`, `partRemoved`, `networkChanged`, `waterDelivered` (part, litres, quality), `valveChanged`, `waterDrawn` (revision 11) |

Built-in capabilities: `conduit`, `meter`, `intake`, `pump`, `valve`, `spray`, `filter`, `outlet`, `controller`,
`fitting`, `drip` (revision 15). Their settings and defaults are listed in the technical specification of the
repository. Revision 15 also adds:

- `spray` settings `loss` (share of the water drawn lost in the air, 0.25 by default: of 10 L, 7.5 L can reach the
  plants; revision 16), `noiseRadius` and `noiseVolume` (what zombies hear at each step while it sprays with a sound, 10 and 10);
- `outlet` settings `costGroup` (outlets of one network with the same group pay their pressure cost once per step,
  together) and `byGravity` (the outlet works on the gravity pressure of a network without pump); outlet type `drip`
  (any water, clean or tainted, group `drip`, works on gravity; ADR-005);
- `fitting` setting `gravity` (pressure a barrel set to Pump gives a network without pump, 1 by default);
- capability `drip` (setting `dose`, 0.2 L): waters the squares beside the part that it is not linked to, without loss.

Revision 16 (ADR-006) adds `flow` to `spray` and `drip`: the litres an irrigation outlet draws per ten-minute step,
thirsty plants or not (absent: the sandbox options `SprinklerFlow`, 10 L, and `DripFlow`, 0.5 L per square); the
plants take what they need, the rest is lost. `controller` setting `duration`: ten-minute steps a timer holds its part
open (3 by default: 30 minutes).

## Example: a part of your own

```lua
-- media/lua/shared/MyMod/MyMod_MiniSprinkler.lua
require "LiveWater/LWT_API"

if LiveWater and LiveWater.API and LiveWater.API.revision >= 8 then
    LiveWater.API.registerPart("MyMod:MiniSprinkler", {
        variants = { off = { "mymod_01_0", "mymod_01_1", "mymod_01_2", "mymod_01_3" },
                     on = { "mymod_01_4", "mymod_01_5", "mymod_01_6", "mymod_01_7" } },
        capabilities = {
            outlet = { type = "sprinkler" },
            valve = { open = false },
            spray = { radius = 1, dose = 0.1 },
        },
    })
end
```

A part whose mod is removed stays inert in the save and comes back with its type when the mod returns.

## Revision history

| Revision | Added |
|---|---|
| 1 | `registerPart`, `registerCapability`, `part`, `LiveWater.Events`; hooks `carries`, `blocks`, `pressurizes`, `ports`, `supply`, `source`, `outlet`, `purifies`, `wear` |
| 2 | field `variants`; hooks `look`, `attach`, `power`, `powered`, `stepped`, `output`, `lines` |
| 3 | filter setting `item`; hooks `cartridge`, `fit`, `unfit`, `actions` |
| 4 | pump upkeep settings; hooks `switchable`, `switch`, `repairable`, `repair`, `sound` |
| 5 | capability `meter`, setting `ports` of `conduit`, quality per part in the `stepped` report |
| 6 | `registerSource`; water quality of an intake from the kind of source found |
| 7 | outlet type as third result of the `outlet` hook; `outcome.outlet` in `stepped`, kept as the outlet state |
| 8 | capability `spray`; hooks `spray`, `jet`, `opened`, `open`; event `valveChanged` |
| 9 | timer (`controller` `timer`: `every`, `watts`, `choices`); hooks `prepare`, `opens`, `timer`, `setTimer`; `choices` of actions; `ctx.hours` |
| 10 | hook `status` (network view); commands `showNetwork` and `network` |
| 11 | capability `fitting`; hooks `draw`, `sense`, `fittingMode`, `setFittingMode`; accepted fluid as fourth result of `outlet`; event `waterDrawn`; quality `fuel`; `registerContainer` |
| 12 | `clean = true` in `registerContainer` |
| 13 | part field `facings` (variant facing by side mask: an inline part turned along its pipe); valve setting `look` (drawn by the valve state, variants `open` / `closed`); spray setting `sound` (loop played while it sprays) |
| 14 | part field `crossings` (sleeve sprites of a shape crossing a fence on its N or W edge; refusal `invalid_crossings`) |
| 15 | capability `drip` (hook `drip`); outlet settings `costGroup` and `byGravity` (hooks `costGroup`, `byGravity`), outlet type `drip`; fitting setting `gravity` (hook `gravity`); spray settings `loss`, `noiseRadius`, `noiseVolume` |
| 16 | spray and drip setting `flow` (fourth result of the `spray` hook, second of `drip`); spray `loss` is a share of the water drawn; controller setting `duration` |
| 17 | `panel` hook of the capabilities: "Information" opens a window instead of the tooltip; part field `bends` (replaced by `branches` in revision 18) |
| 18 | part field `branches`: variant chosen by the mask of the connected sides, relative to the facing (replaces `bends`) |
| 19 | part field `sidesByFacing`: sides the part may connect by, according to the facing it was set down with |

Changes are additive only: a function or field never changes meaning in a later revision. One exception before the
first release: revision 16 made the spray `loss` a share of the water drawn (ADR-006).

Next: [Removing the mod](07-removing-the-mod.md)
