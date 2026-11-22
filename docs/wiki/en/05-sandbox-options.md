# Sandbox options

Page **LiveWater** of the sandbox options (names `LiveWater.<Option>` in the server's `SandboxVars`).

| Option | Default | Range | Effect |
|---|---|---|---|
| Pump flow (`PumpFlowMultiplier`) | 1.0 | 0.1 to 10 | multiplies the litres a pump gives every 10 minutes (50 L at 1.0) |
| Filter cartridge life (`FilterCapacityMultiplier`) | 1.0 | 0.1 to 10 | multiplies the litres a cartridge cleans (500 L at 1.0) |
| Pump wear (`PumpWearMultiplier`) | 1.0 | 0 to 10 | multiplies the efficiency lost while running (about a week from 100% to 0% at 1.0; 0 = no wear) |
| House inlet range (`InletRange`) | 20 | 1 to 100 | squares around an inlet on a map building, on every floor above |
| Base inlet range (`BaseRange`) | 12 | 1 to 50 | squares around an inlet away from a map building (player base) |
| Relay tank size limit (`RelayMaxLitres`) | 300 | 25 to 1000 | largest invisible tank above a fixture, in litres: 25 L, or what the fixture needs at once when a mod says so (Take a Bath and Shower: shower 80 L, bathtub the size of its tub) |
| Fix plumbed washing machines (`WasherFix`) | on | on/off | multiplayer: washing machines fed by an inlet show as plumbed and stop when dry |
| Sprinkler reach (`SprinklerRadiusMultiplier`) | 1.0 | 0.5 to 5 | multiplies the watering radius (2 squares at 1.0, 10 at most) |
| Sprinkler flow (`SprinklerFlow`) | 10 | 0 to 100 | litres an open sprinkler takes every 10 minutes, thirsty plants or not; a quarter is lost in the air, the plants take what they need, the rest is lost |
| Drip line flow (`DripFlow`) | 0.5 | 0 to 10 | litres each drip line square takes every 10 minutes while the network gives it water; the plants beside it take what they need, the rest is lost |
| Sprinkler timer: shortest interval (`SprinklerTimerMin`) | 1 | 1 to 168 | fewest hours a player may set between two waterings |
| Sprinkler timer: longest interval (`SprinklerTimerMax`) | 24 | 1 to 168 | most hours a player may set between two waterings |
| Containers a fill fitting may fill (`FillContainers`) | `WaterDispenser` | text | entity script or sprite names separated by `;`, filled with tainted water like a barrel, whatever their size; barrels, rain collectors and feeding troughs always work |

Mod option (each player, in the game's Mods options): **Animated sprinkler jet**, on by default; untick it for a still
jet on slow computers.

Next: [For modders](06-for-modders.md)
