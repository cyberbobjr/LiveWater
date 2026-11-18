# Changelog

## Unreleased

- Galvanized pipe sections: cut a metal pipe into four sections with a hacksaw.
- Lay a pipe on the ground from the right-click menu, one section per square; pipes join their neighbours and change
  shape on their own (straight, elbow, T, cross). Dismantle a pipe with a pipe wrench to get the section back.
- Pond pump: build it (Electrical 2) and set it down next to a lake, pond or river; it gives 50 L every 10 minutes
  while something needs water and stops on its own otherwise. It needs power: a generator or the grid, or Live Wire
  where Live Wire is enabled (it then shows up in the management software with its state and flow).
- Water filter cartridge: charcoal and cloth, about 500 L of clean water each. Fit, replace or remove it from the
  pond pump's right-click menu; the pump shows it. A cartridge taken out keeps its wear (its condition), a worn one is
  thrown away.
- Pond pump upkeep: turn it on or off from its right-click menu; its efficiency drops while it runs (and the flow
  with it), below 20% it may break down; repair a stopped pump with 2 scrap metal and a wrench. "Information" in its
  menu shows its state, flow, efficiency, filter and source. A running pump hums and draws zombies.
- Shut-off valve: build it from a pipe section and scrap metal with a pipe wrench, set it down between two pipes and
  close it from its right-click menu to cut the water to everything after it (the house, sprinklers further on).
- Water meter: build it and set it inline on a pipe; its "Information" shows the litres that went through it in the
  last 10 minutes and whether the water is clean or unfiltered.
- Wells: a pond pump set down next to a well draws clean water, which reaches the house without a filter.
- House water inlet: build it and set it against the outside wall of a house, then run a pipe to it from the pump. The
  sinks, showers and toilets of that house plumbed with a pipe wrench get running water, up to
  3 floors above (range set in the sandbox options). A green light shows clean water; an amber light means the pump's
  water is unfiltered and the house gets none. Fixtures already fed by something else (a Live Wire pump, a barrel) are
  left alone.
- Barrels connected to the house: right-click a rain collector or barrel inside the house or on its roof and connect
  it to the house water inlet with a pipe wrench, no pipe nor pump needed. It feeds its own floor and the floors below,
  or every floor when a pump is on the inlet's network or the barrel has power. All the barrels drain together; keep
  one in reserve to have it used last. A barrel holding anything but water gives nothing.
- Player bases: an inlet set down away from a map building serves the plumbed fixtures around it (12 squares by
  default, sandbox option), up to 3 floors above. The original fixtures of a nearby map house are left alone.
- A sink, shower or toilet without water says why in its right-click menu (not plumbed, no inlet, unfiltered water,
  low pressure, closed valve, barrels too low or empty...).
- A barrel carried away is no longer connected to its old house.
- Multiplayer fix: washing machines fed by a house water inlet now show as plumbed to the players and stop for
  them when they run out of water, instead of looking stuck (can be turned off in the sandbox options).
- City water: right-click a sink, bathtub, shower, toilet or washing machine you set down inside a building of the map
  and choose "Connect to the City Water" while the city water still runs; it then works like the original fixtures.
- Sprinkler: build it, set it down and feed it with a pipe; open its valve from the right-click menu. Every 10 minutes
  it waters the living plants that need water within 2 squares (sandbox option), 200 ml per dose taken from the pipes;
  unfiltered water is fine for plants. A watering sprinkler shows an animated water jet (a mod option shows a still
  jet instead) and makes the sound of watering.
- Automatic sprinkler: add a timer to a sprinkler (Electrical 2). It opens on its own every 6 hours (choose 1 to 24 h
  from its right-click menu, limits in the sandbox options) to water the plants, then closes. The timer needs a
  little power (generator, grid or Live Wire); without power it does nothing, but you can still open the valve by hand.
- Right-click actions on the water parts now walk you to the part and take a moment (laying or dismantling a pipe a
  little longer).
- A part set down where the network cannot take it (square already used, no free outlet on the pump) now says why.
- Network view: right-click a part and choose "Show the Water Network" to highlight the whole network, coloured by
  state (green: water delivered, red: not enough pressure, amber: unfiltered water refused, grey: closed or dry,
  blue: pipes and pumps), until "Hide the Water Network".
- Barrel fitting: set it between a pipe and a barrel or rain collector. "Fill": the pipes fill the barrel (never
  overflowing); "Pump": the pump draws the barrel instead of its pond. Its look follows the mode and the collector.
- Gasoline: a fitting set to Pump on a gasoline barrel or a gas station pump makes a gasoline network, which only
  fills barrels through fittings set to Fill; houses and sprinklers get nothing and say so.
- A barrel fitting set to Fill also fills a water cooler, with clean water only; more containers can be listed in the
  sandbox options.
- Clean removal: an admin (or the player in solo) can right-click and choose "Remove LiveWater From This World" to
  take every LiveWater part and hidden tank away before unsubscribing, so the save stays readable. A part set down
  afterwards stays a plain decoration you can pick up again.
- The house water inlet also serves the basement (fixtures under the house) and plumbed washing machines.
