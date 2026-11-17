# LiveWater

Project Zomboid Build 42 mod (work in progress): a pond pump, visible pipes with shut-off valves, running water for
the house and sprinklers for the crops, on an open water network that other mods extend through a public API.

- Mod `batman_LiveWater`. LiveWire is optional: with LiveWire (API revision 6 or later) the pump is billed by the
  inverter; without it, the vanilla power rule applies.
- Documentation (French): [docs/](docs/README.md).

Tests: `python -B -m unittest discover -s tests` (needs `pip install lupa`). Mod check: `python -B tools/check_mod.py`.

License: MIT.
