# Getting started

A LiveWater network always has the same shape: a **source** (a pond pump next to water, or a barrel), **pipes** laid
on the ground, and **outlets** at the other end (a house water inlet, sprinklers, barrels to fill). Water moves every
10 in-game minutes.

![The provisional tiles of LiveWater](../../images/art/planche-tuiles-provisoires.png)

Every action from a LiveWater right-click menu walks you to the part and takes a few seconds, like the game's own
actions.

## 1. Cut pipe sections

One pipe section covers one square. Recipe **Cut Pipe Sections**: 1 metal pipe, with a hacksaw (kept), gives
**4 pipe sections**.

> Screenshot to do: the Cut Pipe Sections recipe in the crafting window.

## 2. Build the pond pump

Recipe **Build Pond Pump** (Electrical 2): 1 metal pipe, 2 small metal sheets, 3 electronics scrap, 2 electric wires,
4 screws, with a screwdriver and a wrench (kept). It gives a pond pump (15 kg) and 15 Electrical XP.

Set it down like furniture (right-click it in your inventory, Place) **right next to natural water**: a lake, a pond,
a river, or a well (see [Wells](#12-wells)). Anywhere else the cursor turns red: *Must stand next to natural water*.

The pump needs **power**: a generator or the public grid on its square, or LiveWire (see [LiveWire](04-livewire.md)).
It gives **50 L every 10 minutes** while something downstream needs water, and stops on its own otherwise. A running
pump hums, and the noise draws zombies.

Its right-click menu:

- **Turn Pump On** / **Turn Pump Off**: the switch, on top of the automatic stop.
- **Information**: state (running, on standby, switched off, no power, broken down), flow, efficiency, filter, source.
- **Repair Pump**: see below.

**Wear.** Its efficiency drops while it runs (about a week of running from 100% to 0% with the default settings), and
the flow drops with it. Below 20% it may break down; at 0% it stops. Switch it off, then repair it with **2 scrap
metal** and a **wrench**: efficiency back to 100%.

A pump has 4 connections: up to 4 pipes can leave it. Its pressure is enough for **one house and four sprinklers**
(a house inlet counts 2, a sprinkler or a filling barrel counts 1).

> Screenshot to do: a pond pump on a river bank, running, with its Information lines.

## 3. Lay the pipes

With pipe sections in your inventory, right-click a free square on the ground: **Lay Pipe Section**. One section per
square. Pipes join their neighbours and change shape on their own (straight, elbow, T, cross). Pipes stay on one level:
the house inlet carries the water to the upper floors and the basement.

To take a pipe back: right-click it, **Dismantle Pipe Section**, with a **pipe wrench**. You get the section back.

> Screenshot to do: a pipe line from the pump with an elbow and a T.

## 4. Valves

**Shut-off valve.** Recipe **Build Shut-off Valve**: 1 pipe section, 1 scrap metal, with a pipe wrench (kept). Set it
down with the furniture cursor on an empty square between two pipes of a straight run (it takes the place of one pipe
section: dismantle that section first); it turns along the pipe on its own. It is set down open. Right-click it:
**Close the Valve** cuts the water to everything after it (the house, the sprinklers further on), **Open the Valve**
lets it through again; its handwheel shows the state, and **Information** says it too. Pick it up with a wrench like
the other parts.

Every sprinkler also has its own valve (**Open the Valve** / **Close the Valve**). A closed valve lets no water
through, and the diagnostics say so (*a valve is closed*). Sprinklers are set down closed.

## 5. House water inlet

Recipe **Build House Water Inlet**: 2 pipe sections, 1 small metal sheet, 4 screws, with a pipe wrench (kept).

Set it down **against the outside wall** of a building of the map, and run a pipe to it from the pump. It feeds the
**sinks, bathtubs, showers, toilets and washing machines** of that building that you plumbed with a pipe wrench (the
game's own Plumb action), within **20 squares** (sandbox option), up to **3 floors above** it and **2 basement levels**
below.

Its light tells you what it does:

- **green**: clean water, the house gets it;
- **amber**: the pump's water is **unfiltered**, the house gets **none** (fit a filter, or use a well).

A fixture already fed by something else (a LiveWire pump, a barrel above it) is left alone.

> Screenshot to do: the house water inlet against a wall, green light, and a sink with running water.

## 6. Water filter

Pond and river water is not clean. Recipe **Make Water Filter**: 2 charcoal and 2 ripped sheets give a **water filter
cartridge**. It cleans about **500 L**; its condition shows what is left.

Right-click the pump: **Fit Water Filter**, **Replace Water Filter** or **Remove Water Filter**. A cartridge taken out
keeps its wear; a worn-out one is thrown away. The pump shows the filter on its tile.

## 7. Sprinklers

**Manual sprinkler.** Recipe **Build Sprinkler**: 2 pipe sections, 1 scrap metal, 1 plank, with a pipe wrench (kept).
Set it down like furniture and feed it with a pipe. Right-click: **Open the Valve**. Every 10 minutes it waters the
living plants that need water within **2 squares** (sandbox option), 200 ml per dose taken from the pipes. Unfiltered
water is fine for plants. A watering sprinkler shows an animated water jet (mod option *Animated sprinkler jet*: untick
it for a still jet on slow computers) and you hear it water.

**Automatic sprinkler.** Recipe **Add a Timer to a Sprinkler** (Electrical 2): 1 sprinkler, 2 electronics scrap,
1 electric wire, with a screwdriver (kept); 10 Electrical XP. It opens on its own **every 6 hours**, waters the plants,
then closes. Change the interval from its right-click menu, **Watering Timer**, 1 to 24 hours (limits in the sandbox
options). The timer needs a little power (5 W: generator, grid or LiveWire); without power it does nothing, but you
can still open the valve by hand.

> Screenshot to do: an automatic sprinkler watering a garden, jet visible.

## 8. Barrel fitting: Fill or Pump

Recipe **Build Barrel Fitting**: 1 pipe section, 1 rubber hose, with a pipe wrench (kept). Set it down between the end
of a pipe and a barrel or rain collector. Right-click it:

- **Set to Fill**: the pipes fill the barrel, up to 50 L every 10 minutes, never overflowing. A water cooler can be
  filled the same way, with clean water only.
- **Set to Pump**: the pump of the network draws the barrel instead of its pond.

Its look follows the mode and the shape of the collector. **Information** shows the mode and the litres in the barrel.

**Gasoline.** A fitting set to Pump on a gasoline barrel or a gas station pump makes a gasoline network. It only fills
barrels (empty, or already holding gasoline) through fittings set to Fill. House inlets and sprinklers get nothing and
say so.

## 9. Barrels connected to the house

No pump? Right-click a rain collector or a barrel standing **inside the house or on its roof**: **Connect to the House
Water Inlet** (with a pipe wrench). No pipe is needed, only a house water inlet on that building.

- A barrel feeds **its own floor and the floors below** (gravity). With a pump on the inlet's network, or power on the
  barrel's square, it feeds every floor.
- All connected barrels drain **together**. **Keep in Reserve (used last)** sets one aside: it is used only once the
  others are empty. **Use With the Other Barrels** puts it back.
- An empty barrel stays connected. A barrel holding anything other than water gives nothing until it is emptied.
- **Disconnect from the House Water Inlet**, or carry the barrel away: it is no longer connected.

## 10. City water

While the city water still runs, right-click a sink, bathtub, shower, toilet or washing machine that **you set down**
inside a room of a building of the map: **Connect to the City Water**. It then works like the original fixtures:
unlimited water until the city water is cut off.

## 11. Water meter

Recipe **Build Water Meter**: 1 pipe section, 1 small metal sheet, 2 screws, with a screwdriver (kept). Set it down
inline on a pipe; it follows the pipe's direction. **Information** shows the litres that went through it in the last
10 minutes, and the fluid (clean water, unfiltered water or gasoline).

## 12. Wells

The same pond pump set down next to a **well** draws **clean water**: the house gets it without a filter. Its
Information says *Source: well (clean water)*.

> Screenshot to do: a pond pump next to a well.

Next: [Player base](02-player-base.md) · [Diagnostics](03-diagnostics.md)
