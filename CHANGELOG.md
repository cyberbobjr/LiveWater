# Changelog

## Unreleased

- Galvanized water pipes: cut a metal pipe into four pipes with a hacksaw.
- Pipes are placed with the "Place" menu like every other LiveWater equipment, one per square; they join their
  neighbours and change shape on their own (straight, elbow, T, cross). Pick a pipe up with a wrench.
- Pipes pass under fences, low or tall, and gates (a dark sleeve shows where they cross), but never through a solid
  wall or a door: to bring water inside a house, use the house water inlet.
- Pond pump: build it (Electrical 2) and set it down next to a lake, pond or river; it gives 50 L every 10 minutes
  while something needs water and stops on its own otherwise. It needs power: a generator or the grid, or Live Wire
  where Live Wire is enabled (it then shows up in the management software with its state and flow).
- Water filter cartridge: charcoal and cloth, about 500 L of clean water each. It goes in the house water inlet:
  fit, replace or remove it from the inlet's right-click menu, and the inlet shows it. It cleans only the water that
  enters the house, so watering never wears it. A cartridge taken out keeps its wear (its condition).
- Water filter cartridge: a worn-out cartridge taken out of the house inlet comes back as a Spent Water Filter Cartridge; recharge it with 2 charcoal and 1 ripped sheet (recipe "Recharge Water Filter Cartridge"), or dismantle it for its cloth.
- Pond pump upkeep: turn it on or off from its right-click menu; its efficiency drops while it runs (and the flow
  with it), below 20% it may break down; repair a stopped pump with 2 scrap metal and a wrench. Zombies hear it only
  while it pumps.
- Shut-off valve: build it from a pipe and scrap metal with a pipe wrench, set it down between two pipes and
  close it from its right-click menu to cut the water to everything after it (the house, sprinklers further on).
- Water meter: build it and set it inline on a pipe.
- Wells: a pond pump set down next to a well draws clean water, which reaches the house without a filter.
- House water inlet: build it and set it against the outside wall of a house, then run a pipe to it from the pump. The
  sinks, showers and toilets of that house plumbed with a pipe wrench get running water, up to
  3 floors above (range set in the sandbox options). A green light shows clean water (a working filter in the inlet, or a
  well); an amber light means the water is unfiltered and the house gets none. Fixtures already fed by something else (a Live Wire pump) are
  left alone.
- Barrels reach the house only through a barrel fitting on a pipe and a pump: without a pump, a barrel only feeds drip lines.
- Player bases: an inlet set down away from a map building serves the plumbed fixtures around it (12 squares by
  default, sandbox option), up to 3 floors above. The original fixtures of a nearby map house are left alone.
- A sink, shower or toilet without water says why in its right-click menu (not plumbed, no inlet, unfiltered water,
  low pressure, closed valve...).
- Multiplayer fix: washing machines fed by a house water inlet now show as plumbed to the players and stop for
  them when they run out of water, instead of looking stuck (can be turned off in the sandbox options).
- City water: right-click a sink, bathtub, shower, toilet or washing machine you set down inside a building of the map
  and choose "Connect to the City Water" while the city water still runs; it then works like the original fixtures.
- Sprinkler: build it, set it down and feed it with a pipe (it turns to face its pipe on its own); open its valve
  from the right-click menu. While its valve is open it sprays 10 L every 10 minutes, whether the plants are thirsty
  or not; the living plants that need water in the 5 x 5 square around it (2 squares on each side, sandbox option)
  take 200 ml doses of it, nearest first, and the rest is lost. Any water will do, clean or not. Close it when the
  garden is watered, or it keeps emptying your barrel. Right-click a sprinkler or a
  drip line and choose "Show All Watered Areas" to light up the floor of every square watered around you ("Hide the
  Watered Area" turns it off). Its
  Information gives its flow (litres every 10 minutes, and how many reach the plants). A watering sprinkler shows an animated water jet that turns all the way round (a mod option shows a still jet
  instead) and makes the sound of watering.
- A sprinkler loses a quarter of its water in the air: of 10 L, 7.5 L can reach the plants. Zombies hear it every 10
  minutes while it sprays.
- Automatic sprinkler: add a timer to a sprinkler (Electrical 2). It opens on its own every 6 hours (choose 1 to 24 h
  from its right-click menu, limits in the sandbox options) and sprays for 30 minutes, then closes. The timer needs a
  little power (generator, grid or Live Wire); without power it does nothing, but you can still open the valve by hand.
- Drip line: a thin hose laid on the ground between your rows that waters the plants on both sides of it, quietly and
  without wasting water. Recipe "Make Drip Lines" (Farming): 1 rubber hose, 2 uses of duct tape and a sharp knife give
  4 drip lines. Place them like pipes, one per square, and pick them up by hand; they join the water pipes. They water
  with any water, clean or not (no filter needed; gasoline and other fluids are refused), and all the drip lines of a
  network take very little pressure. Each square of line takes 0.5 L every 10 minutes while the network gives it
  water; the plants beside it take what they need, the rest soaks away. A drip line at the far end of a network
  that ran out of pressure stays dry.
- Sandbox options "Sprinkler flow" (10 L by default) and "Drip line flow" (0.5 L per square by default) set how much
  water they take every 10 minutes. One pond pump (50 L) feeds up to five sprinklers in full; the next ones get
  what is left, then nothing.
- No pump? A barrel connected with a fitting set to Pump feeds drip lines by its own weight, rain or pond water
  alike. That is only enough for drip lines: sprinklers and houses on that network get nothing.
- Right-click actions on the water parts now walk you to the part and take a moment.
- A part set down where the network cannot take it (square already used, no free outlet on the pump) now says why.
- A wall torn down between a pipe and a valve (or pump) whose connections are all taken no longer joins them: the
  part set down last stays apart, also after reloading the game.
- Network view: right-click a part and choose "Show the Water Network" to highlight the whole network, coloured by
  state (green: water delivered, red: not enough pressure, amber: unfiltered water refused, grey: closed or dry,
  blue: pipes and pumps), until "Hide the Water Network".
- Barrel fitting: set it between a pipe and a barrel or rain collector. "Fill": the pipes fill the barrel (never
  overflowing); "Pump": the pump draws the barrel instead of its pond. Its look follows the mode and the collector.
- Gasoline: a fitting set to Pump on a gasoline barrel or a gas station pump makes a gasoline network, which only
  fills barrels through fittings set to Fill; houses and sprinklers get nothing and say so.
- A barrel fitting set to Fill always pours tainted water, even from a well: the pipes carry untreated water, only the
  house inlet gives clean water. It also fills a water cooler the same way; more containers can be listed in the
  sandbox options.
- Clean removal: an admin (or the player in solo) can right-click and choose "Remove LiveWater From This World" to
  take every LiveWater part and hidden tank away before unsubscribing, so the save stays readable. A part set down
  afterwards stays a plain decoration you can pick up again.
- The house water inlet also serves the basement (fixtures under the house) and plumbed washing machines.
- Your water network keeps working while you are far away: pumps, sprinklers, drip lines and barrels go on, the house
  inlet waits for your return, and a generator counts as it was when you left.
- Dismantling: every LiveWater part has a "Dismantle" recipe (pipe wrench, screwdriver or knife). It gives back scrap,
  never more than the part cost; a water filter gives back cloth. Parts set down can also be dismantled where they
  stand with the game's Disassemble menu (all but the drip line, which you pick up first).
- Loot: water pipes, valves and barrel fittings can now be found, rarely, in plumbing supplies and tool crates;
  sprinklers, drip lines and water filters in garden stores and farming supplies.
- Barrel fitting: water now flows through it from one pipe to the next (it fills or drains its barrel and passes the
  rest on); it is drawn straight, bent, as a tee or as a cross to match the pipes around it (the barrel stays behind it).
- Water meter and inline valve stay straight: only the two pipes on the axis they were set down along connect to them;
  a pipe laid against their side stays apart. The valve keeps that axis when opened or closed.
- Item names: the valve, house inlet, sprinklers, automatic sprinkler and barrel fitting now show their name in the
  inventory in every language.
- "Show the Water Network" and "Hide the Water Network" (and the watered area options) no longer show together: one at
  a time.
- Water meter: it counts the litres since it was set down (kept when picked up); "Information" opens a US-style water
  meter with rolling digits and a sweep hand (one turn every 10 L), the last 10 minutes and the water quality.
- Pond pump: "Information" opens a backlit LCD screen: state, possible flow, flow of the last 10 minutes, total pumped,
  efficiency, source.
- A sink, shower, bathtub, toilet or washing machine fed by a house water inlet shows the water it holds in its
  right-click menu (e.g. "Water: 18 L / 25 L").
- The water network view also colours the fixtures of the house: green with water, red connected but dry, amber not
  plumbed, grey fed by something else.
- Sprinklers are easier to read: a bigger lever on the manual sprinkler (along the pipe when open, across when closed),
  a green light on the automatic sprinkler's timer while it waters.
- Opening or closing a valve (inline or sprinkler) makes a valve sound heard by nearby players.
- The pond pump hums as long as it is switched on and has current, and goes quiet the moment its generator stops or the
  grid goes off (zombies still hear it only while it pumps).
