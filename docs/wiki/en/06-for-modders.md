# For modders: the public API

LiveWater is an **open water network**, built like Live Wire: **producers** put water into the pipes, **consumers**
take it out, and both are registered through the same public API another mod uses. A new part is a data file; a new
behaviour is a capability.

## Rules

- Register from a file in `media/lua/shared`, while the game loads, **before `OnInitGlobalModData`**. Afterwards every
  registration is refused with `registration_closed`.
- Every refusal returns `false` and a reason, and writes an English warning in the console. Nothing throws.
- Ids are namespaced: `"<YourMod>:<Name>"`.
- Check `LiveWater.API.revision` before using a function or field added after revision 1. The current revision is **22**.

## Functions

| Function | Role |
|---|---|
| `LiveWater.API.registerPart(id, definition)` | a new part type: `sprites` (`{ [mask] = sprite }`, masks 0-15, redrawn by the connections) or `variants` (sprites chosen by state, 4 facings S, E, N, W), `crossings` (revision 14: `{ [mask] = { [edges] = sprite } }`, edges 1 = N, 8 = W, 9 = both, within the mask: the shape drawn with a sleeve where it crosses a fence carried by its own N or W edge; refused as `invalid_crossings`), `sides` (connectable sides mask, 15 by default), `capabilities` (`{ kind = settings or true }`) |
| `LiveWater.API.registerCapability(kind, implementation)` | a new capability; `implementation.define(params)` is required, every hook is optional |
| `LiveWater.API.part(id)` | a checked copy of a part definition, or `nil` |
| `LiveWater.API.registerSource(kind, definition)` | revision 6: a kind of water a producer can draw from (a source next to the pump) `{ quality = "clean" or "tainted", flag = IsoFlagType of a nearby square, sprites = { nearby object sprites } }` |
| `LiveWater.API.registerContainer(name, definition)` | revision 11: a container a fill fitting fills, or a pump draws from (`vessel`), by sprite or entity name, `{ shape = "tall" or "low" }`; filled like a barrel, with tainted water (ADR-005 D07; the field `clean` of revision 12 is ignored) |
| `LiveWater.API.registerOutlet(outletType, handler)` | revision 22: a consumer, `outletType` `"<YourMod>:<Name>"`, see below |
| `LiveWater.Events.on(name, fn)` / `off(name, fn)` | events on the authority: `partAdded`, `partRemoved`, `networkChanged`, `waterDelivered` (part, litres, quality), `valveChanged`, `waterDrawn` (revision 11) |

Built-in capabilities: `conduit`, `meter`, `intake`, `pump`, `valve`, `spray`, `filter`, `outlet`, `controller`,
`fitting`, `drip` (revision 15), `vessel` (revision 21). Their settings and defaults are listed in the technical
specification of the repository.

## Producers and consumers

A **producer** puts water into the pipes of its network. The water pump is one: a part with the `pump` capability,
with `intake` where it draws from a source. A producer draws only from what it touches, and only a producer adds water;
a network without a producer gives nothing.

A **consumer** takes out of the network the fluid it accepts, water by default: the house inlet, the sprinklers, the drip lines and the fill fittings
are built in; yours is registered with `registerOutlet`. The network says how much a consumer may take and gives it the
litres; the consumer decides what they do with them.

Producers and consumers run on the authority only: the server, or the game in solo.

- `intake` (field `orVessel`, revision 21): `quality` `"clean"` or `"tainted"`; `orVessel = true` lets the
  part stand against a container (a barrel, a rain collector, a water cooler, a feeding trough) with no other source.
- `vessel` (revision 21): `rate`, the litres a step at most (50 by default). The part draws the water of the container
  set against it. Water is drawn, clean or tainted; from revision 23, fuel too (a pump against a gas station fuel pump), never another fluid.
- `outlet` (revision 22): `type` may be `"<YourMod>:<Name>"`, the name of a consumer registered with `registerOutlet`.
- `outlet` (revision 23): `takes`, the fluid the consumer accepts: `"water"` (the default: an outlet without it gets water only), `"fuel"`, `"other"` or `"any"`. An outlet given a fluid it does not take gets the state `wrong_fluid`. It is the fourth result of the `outlet` hook.
- `stepped` hook (revision 23): `outcome.otherFluid = true` for a pump that gave nothing this step because another fluid is in the pipes of its zone (the first pump placed in the zone sets the fluid).
- `sense` hook (revision 23): `info.takes` says what an empty container takes (`"water"` for a feeding trough).

### `registerOutlet` (revision 22)

`LiveWater.API.registerOutlet(outletType, handler)` says where the water of an outlet type goes. The handler is called
with `:` on the authority:

- `need(part)`: required. The litres the outlet wants this step.
- `deliver(part, litres, quality)`: required. The litres it was given, and their quality (`"clean"` or `"tainted"`).
- `release(part)`: optional. The part left the world (picked up or removed).
- `cut(part)`: optional. A valve just cut the outlet off from the water.

Returns `true`, or `false` and `"registration_closed"`, `"invalid_type"`, `"invalid_handler"` or `"duplicate_outlet"`.
The built-in types `houseInlet`, `sprinkler`, `drip` and `barrelFill` are reserved.

### Example: a feeding trough of your own

```lua
-- media/lua/shared/MyMod/MyMod_Trough.lua
require "LiveWater/LWT_API"

if LiveWater and LiveWater.API and LiveWater.API.revision >= 22 then
    LiveWater.API.registerPart("MyMod:Trough", {
        variants = { off = { "mymod_trough_0", "mymod_trough_1", "mymod_trough_2", "mymod_trough_3" } },
        capabilities = {
            outlet = { type = "MyMod:Trough" },
        },
    })

    LiveWater.API.registerOutlet("MyMod:Trough", {
        need = function(self, part)
            return 20 -- litres this trough takes at this step
        end,
        deliver = function(self, part, litres, quality)
            -- add the litres to the trough's tank; keep the quality (tainted water stays tainted)
        end,
        cut = function(self, part)
            -- a valve closed: the trough gets no water until it opens
        end,
    })
end
```

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
| 15 | capability `drip` (hook `drip`); outlet setting `costGroup` (hook `costGroup`), outlet type `drip`; spray settings `loss`, `noiseRadius`, `noiseVolume` |
| 16 | spray and drip setting `flow` (fourth result of the `spray` hook, second of `drip`); spray `loss` is a share of the water drawn; controller setting `duration` |
| 17 | `panel` hook of the capabilities: "Information" opens a window instead of the tooltip; part field `bends` (replaced by `branches` in revision 18) |
| 18 | part field `branches`: variant chosen by the mask of the connected sides, relative to the facing (replaces `bends`) |
| 19 | part field `sidesByFacing`: sides the part may connect by, according to the facing it was set down with |
| 20 | filter setting `spent` (item a worn-out cartridge comes back as, ADR-009 D01); fourth result of the `cartridge` hook |
| 21 | capability `vessel` (`rate`; hooks `sense`, `draw`, `lines`); intake field `orVessel`; `GameSite:hasVessel()` |
| 22 | `registerOutlet` and outlet types `"<YourMod>:<Name>"`; the fill fitting only fills (hook `container` replaces `fittingMode`); no gravity flow: only a producer puts water into a network (fitting and outlet settings `gravity` and `byGravity` removed) |
| 23 | outlet field `takes` (fluid a consumer accepts; fourth result of the `outlet` hook); capability `vessel` also draws fuel; `outcome.otherFluid` of `stepped`; `info.takes` of `sense`; one fluid per network zone and step (ADR-014) |

Changes are additive only: a function or field never changes meaning in a later revision. Two exceptions before the
first release: revision 16 made the spray `loss` a share of the water drawn (ADR-006), and revision 22 removed the
gravity flow and the fitting modes (ADR-012).

Next: [Removing the mod](07-removing-the-mod.md)
