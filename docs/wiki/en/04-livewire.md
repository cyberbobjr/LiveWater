# LiveWire (optional)

LiveWater works on its own: a pump runs when its square has power from a generator or the public grid, like any
appliance of the game.

With **LiveWire** enabled (API revision 6 or later), LiveWater registers its powered parts as LiveWire consumers:

- the **pond pump** draws **250 W** while it runs, from the LiveWire inverter that powers its square; a LiveWire
  breaker can cut it;
- the **timer of an automatic sprinkler** draws **5 W**;
- the LiveWire management software shows each pump (state, flow) and the total of the pumps (*Water pumps running*,
  *Water pumped per 10 minutes*).

A sink fed by a LiveWire water pump is left alone by the LiveWater house inlet: the two mods do not fill the same
fixture twice.

No setting is needed: LiveWater detects LiveWire when the world starts.

Next: [Sandbox options](05-sandbox-options.md)
