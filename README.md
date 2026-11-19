# LiveWater

Project Zomboid Build 42.22 mod: a water pump set by water, against a barrel or a gas station pump, visible pipes, running water for the house, a fill
fitting that fills barrels, rain collectors and feeding troughs, city water for the fixtures you set down, and sprinklers for the crops,
on an open water network (producers and consumers, like Live Wire) that other mods extend through a public API. Singleplayer and multiplayer (multiplayer checked by automated in-game runs only). Translated into 11 languages.

- Mod `batman_LiveWater`. LiveWire is optional: with LiveWire (API revision 6 or later) the pump and the sprinkler
  timers are billed by its inverter; without it, the vanilla power rule applies.
- Not compatible with LG Extended Plumbing, LG Connect To Water Supply and Plysken Irrigation Pipes.
- Player guide: [wiki (English)](docs/wiki/en/Home.md), [wiki (français)](docs/wiki/fr/Home.md).
- Modders: [public API](docs/wiki/en/06-for-modders.md).
- Development documentation (French): [docs/](docs/README.md). Changes: [CHANGELOG.md](CHANGELOG.md).

Tests: `python -B -m unittest discover -s tests` (needs `pip install lupa`). Mod check: `python -B tools/check_mod.py`
(Lua syntax and load order, server guards, no per-frame events, translation parity of the 11 languages).

License: MIT.
