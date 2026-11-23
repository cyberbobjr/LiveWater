# Multiplayer

> LiveWater's multiplayer has been checked by automated in-game runs (dedicated server and client), not yet on a live public server. Report what you see.

- The **server decides everything**: it moves the water every 10 minutes, saves the networks and checks every action
  (distance, items, tools, admin rights). Players only send requests from their right-click menus.
- Every player sees the same tiles: pump on or off, inlet light and filter, sprinkler jet.
- Add LiveWater to the server's `Mods=` line and to `WorkshopItems=`. The tiles (`batman_livewater_01`) come with the mod.
- LiveWater is **incompatible** with *LG Extended Plumbing* and *LG Connect To Water Supply*: both change the water
  source of fixtures, and two such mods would fill the same sink twice. LiveWater covers what they do.
- LiveWater is also **incompatible** with *Plysken Irrigation Pipes*: it lays its own irrigation pipes, fed by rain
  barrels, that water crops; LiveWater's pipes, sprinklers and drip lines do the same job.
- The sandbox option *Fix plumbed washing machines* (on by default) fixes a game bug on servers: washing machines
  fed by a house inlet show as plumbed to the players and stop when they run out of water.
- The sandbox limits of the sprinkler timer are checked by the server (*This interval is not allowed on this server.*).
- Removing the mod is an admin action: see [Removing the mod](07-removing-the-mod.md).

[Home](Home.md)
