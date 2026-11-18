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
| `LiveWater.API.registerPart(id, definition)` | a new part type: `sprites` (`{ [mask] = sprite }`, masks 0-15, redrawn by the connections) or `variants` (sprites chosen by state, 4 facings S, E, N, W), `sides` (connectable sides mask, 15 by default), `capabilities` (`{ kind = settings or true }`) |
| `LiveWater.API.registerCapability(kind, implementation)` | a new capability; `implementation.define(params)` is required, every hook is optional |
| `LiveWater.API.part(id)` | a checked copy of a part definition, or `nil` |
| `LiveWater.API.registerSource(kind, definition)` | revision 6: a kind of water source `{ quality = "clean" or "tainted", flag = IsoFlagType of a nearby square, sprites = { nearby object sprites } }` |
| `LiveWater.API.registerContainer(name, definition)` | revision 11: a container a barrel fitting can fill, by sprite or entity name, `{ shape = "tall" or "low" }`; revision 12: `clean = true` (clean water only) |
| `LiveWater.Events.on(name, fn)` / `off(name, fn)` | events on the authority: `partAdded`, `partRemoved`, `networkChanged`, `waterDelivered` (part, litres, quality), `valveChanged`, `waterDrawn` (revision 11) |

Built-in capabilities: `conduit`, `meter`, `intake`, `pump`, `valve`, `spray`, `filter`, `outlet`, `controller`,
`fitting`, `layable`. Their settings and defaults are listed in the technical specification of the repository.

## Example: a part of your own

```lua
-- media/lua/shared/MyMod/MyMod_DripLine.lua
require "LiveWater/LWT_API"

if LiveWater and LiveWater.API and LiveWater.API.revision >= 8 then
    LiveWater.API.registerPart("MyMod:DripLine", {
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
| 1 | `registerPart`, `registerCapability`, `part`, `LiveWater.Events`; hooks `carries`, `blocks`, `pressurizes`, `ports`, `supply`, `source`, `outlet`, `purifies`, `wear`, `layable` |
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

Changes are additive only: a function or field never changes meaning in a later revision.

Next: [Removing the mod](07-removing-the-mod.md)
