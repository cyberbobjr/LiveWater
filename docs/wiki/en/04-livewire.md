# LiveWire (optional)

LiveWater works on its own: a pump runs when its square has power from a generator or the public grid, like any
appliance of the game.

With **LiveWire** enabled (API revision 6 or later), LiveWater registers its powered parts as LiveWire consumers:

- the **water pump** draws **150 W** while it runs, from the LiveWire inverter that powers its square; a LiveWire
  breaker can cut it;
- the **timer of an automatic sprinkler** draws **5 W**;
- the LiveWire management software shows each pump (state, flow) and the total of the pumps (*Water pumps running*,
  *Water pumped per 10 minutes*).

### Wiring the pump to an inverter (LiveWire 2.x)

With LiveWire 2.x (API revision 9 or later), the water pump can be **connected to an inverter with electric wire**,
like a LiveWire appliance:

- right-click the pump, **LiveWire > Connect to an inverter**; or, from the inverter, **Connect equipment** or the
  **Connections** window;
- you need **Electrical 2**, a **screwdriver** and **electric wire** for the distance, up to the cable range
  (**12 tiles** by default), even outside the inverter's powered area: a pump at the pond, the inverter in the house;
- once connected, the pump runs on that inverter and its draw is billed to it, even while nobody is near.

A pump that is not connected (or with an older LiveWire, or without LiveWire) uses the power of its square: a
generator, the public grid or the area of an inverter. The automatic sprinkler timer cannot be connected: it always
uses the power of its square.

A sink fed by a LiveWire water pump is left alone by the LiveWater house inlet: the two mods do not fill the same
fixture twice.

No setting is needed: LiveWater detects LiveWire when the world starts.

Next: [Sandbox options](05-sandbox-options.md)
