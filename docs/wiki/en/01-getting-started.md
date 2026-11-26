# Getting started

A LiveWater network always has the same shape: a **producer**, a **water pump** set next to water (a lake, a pond, a
river, a well) or against a barrel; **pipes** set down on the ground; and **outlets** at the other end (a house water
inlet, sprinklers, drip lines, and the **fill fittings** that fill a barrel, a rain collector or a feeding trough). Only
a pump puts water into the network. Water moves every 10 in-game minutes.

![The provisional tiles of LiveWater](../../images/art/planche-tuiles-provisoires.png)

Every action from a LiveWater right-click menu walks you to the part and takes a few seconds, like the game's own
actions.

## 1. Cut water pipes

One water pipe covers one square. Recipe **Cut Pipe Sections**: 1 metal pipe, with a hacksaw (kept), gives
**4 water pipes**.

> Screenshot to do: the Cut Pipe Sections recipe in the crafting window.

## 2. Build the water pump

Recipe **Build Water Pump** (Electrical 2): 1 metal pipe, 2 small metal sheets, 3 electronics scrap, 2 electric wires,
4 screws, with a screwdriver and a wrench (kept). It gives a water pump (15 kg) and 15 Electrical XP.

Set it down like furniture (right-click it in your inventory, Place) **right next to natural water**: a lake, a pond,
a river, or a well (see [Wells](#12-wells)); or **against a barrel** or **against a gas station pump** (see below). Anywhere else the cursor turns red:
*Must stand next to natural water (lake, pond, river), against a well, a barrel or a gas station pump.*

**Against a barrel.** The pump can also stand against a barrel on any of its four sides: a barrel or a rain collector
holding 20 L or more, a water cooler, a container listed in the sandbox options, or a feeding trough. It then pumps the
barrel's water into the pipes, up to its flow (50 L every 10 minutes). It pumps water only, never fuel, and the water
keeps its quality: tainted water passes, and the house needs the filter of its inlet. An empty barrel gives nothing.

Two pumps of the same liquid on one network add their flows (100 L every 10 minutes for two), and each one draws only its own source: a
pump by a pond never empties the barrel of a pump set against a barrel. A pump that touches both a barrel and a pond
empties the barrel first, then uses the pond.

**Against a gas station pump.** The pump can also stand against a gas station fuel pump (the vanilla Fossoil and Gas-2-Go pumps). It then pumps the station's gasoline into the pipes, up to its flow (50 L every 10 minutes), with power like always, and the station's stored fuel goes down. An empty station gives nothing.

**One liquid per network.** A network carries one liquid at a time: the first pump placed sets it (water, clean or tainted, or gasoline). A pump of another liquid gives nothing, and its information says *Pump: another liquid is in the pipes*. To have both, make two networks, or close a valve between the pumps: each side has its own first pump.

Consumers take only what they accept. The house water inlet, the sprinklers and the drip lines take water only: with gasoline in the pipes they take nothing and say *This is not water*. The fill fitting never mixes: it fills an empty container with whatever the pipes carry, a container of water with water only, a container of gasoline with gasoline only. It never fills a feeding trough with anything but water, and it never fills a gas station pump.

The pump needs **power**: a generator or the public grid on its square, or LiveWire (see [LiveWire](04-livewire.md)).
It gives **50 L every 10 minutes** while something downstream needs water, and stops on its own otherwise. A pump that is
switched on and has power hums, even with no water asked for; the noise draws zombies only while it pumps.

Its right-click menu:

- **Turn Pump On** / **Turn Pump Off**: the switch, on top of the automatic stop.
- **Information**: a backlit LCD screen: state (running, on standby, switched off, no power, broken down), possible
  flow, flow of the last 10 minutes, total pumped since it was set down, efficiency, source. When a barrel stands
  against it, a line **Barrel: N L** gives the litres it holds. The screen updates while it is open.
- **Repair Pump**: see below.

**Wear.** Its efficiency drops while it runs (about a week of running from 100% to 0% with the default settings), and
the flow drops with it. Below 20% it may break down; at 0% it stops. Switch it off, then repair it with **2 scrap
metal** and a **wrench**: efficiency back to 100%.

A pump has 4 connections: up to 4 pipes can leave it. Its pressure is enough for **one house and four sprinklers**
(a house inlet counts 2, a sprinkler or a fill fitting counts 1, all the drip lines of the network together
count 1).

**While you are away.** Your water network keeps working when you go far from it: the pump still draws from its pond,
well or barrel, open sprinklers and drip lines still water the crops, and barrels filled through a fill fitting keep
filling (you find the right amount when you come back). The house inlet waits for your return. Power while you are
away: with LiveWire, the network that powers the pump's square; otherwise the public grid until its shut-off day,
and a generator counts as it was when you left (it burns no fuel meanwhile and picks up its consumption when you
return).

![A water pump running on a river bank, on its generator](../../images/screenshots/pump-running.jpg)

![The LCD screen of a running pump](../../images/screenshots/pump-info-en.jpg)

## 3. Set down the pipes

A water pipe is set down like every other part: right-click it in your inventory, **Place**, then put it down with the
furniture cursor. One pipe per square. Pipes join their neighbours and change shape on their own (straight, elbow, T, cross). Pipes stay on one level:
the house inlet carries the water to the upper floors and the basement.

Pipes pass under fences and gates (a dark sleeve shows where they cross), but not through a solid wall or a door.
To bring water into a building, use the house water inlet.

A pipe set down against the side of a water meter or an inline valve does not join it: both have two sides only, on
the axis they were set along.

**Network view.** Right-click a part and choose **Show the Water Network** to colour the whole network: pipes and pumps
in blue, outlets by state, and the house fixtures they feed (see [Diagnostics](03-diagnostics.md)). **Hide the Water
Network** turns it off; the two options are never shown together.

To take a pipe back, pick it up like the other parts, with a **wrench**. You get the pipe back.

![A pipe line from the pump to a house, with a water meter and a valve](../../images/screenshots/pipe-line.jpg)

## 4. Valves

**Shut-off valve.** Recipe **Build Shut-off Valve**: 1 water pipe, 1 scrap metal, with a pipe wrench (kept). Set it
down with the furniture cursor on an empty square between two pipes of a straight run (it takes the place of one pipe:
pick that pipe up first); it turns along the pipe on its own. It is set down open. Right-click it:
**Close the Valve** cuts the water to everything after it (the house, the sprinklers further on), **Open the Valve**
lets it through again; its handwheel shows the state, and **Information** says it too. It acts at once, like the valve
of a sprinkler: the water stops or flows again right away, and the taps of a house cut off run dry (the water left in
the pipes is lost). Pick it up with a wrench like the other parts.

Every sprinkler also has its own valve (**Open the Valve** / **Close the Valve**). A closed valve lets no water
through, and the diagnostics say so (*a valve is closed*). Sprinklers are set down closed.

An inline valve keeps its axis when you open or close it. Opening or closing a valve, inline or on a sprinkler, makes
a valve sound that nearby players hear.

## 5. House water inlet

Recipe **Build House Water Inlet**: 2 water pipes, 1 small metal sheet, 4 screws, with a pipe wrench (kept).

Set it down **against the outside wall** of a building of the map, and run a pipe to it from the pump. It feeds the
**sinks, bathtubs, showers, toilets and washing machines** of that building that you plumbed with a pipe wrench (the
game's own Plumb action), within **20 squares** (sandbox option), on **every floor above** it and **2 basement levels**
below.

The **pipe wrench** works from your bag: the game equips it for you. It has to be **unbroken** — a broken one no longer
counts, and a plain wrench does not do.

Its light tells you what it does:

- **green**: clean water, the house gets it (a working filter in the inlet, or water from a well);
- **amber**: the water is **unfiltered**, the house gets **none** (fit a filter in the inlet, replace a worn-out one,
  or use a well).

A fixture already fed by something else (a LiveWire pump) is left alone.

**On a roof:** the game only offers **Plumb** inside a room. LiveWater offers the same option for a fixture set down
on a roof (in the open, right above a room) once an inlet reaches it. The inlet of a map building also serves the
storeys you built on top of it. A fixture in the garden, with no room under it, cannot be plumbed.

![A summer kitchen on a flat roof: counters, a plumbed sink, barbecues, a table](../../images/screenshots/rooftop-kitchen.jpg)

**Unplumb:** right-click a plumbed fixture with a pipe wrench in your bag and choose **Unplumb**. The fixture stops
giving water and can be plumbed again. Picking a fixture up or dismantling it also takes its plumbing away: plumb it
again where you set it down.

A sink, shower, bathtub, toilet or washing machine that this inlet feeds shows the water it holds in its right-click
menu, for example a greyed line **Water: 18 L / 25 L**.

![The house water inlet against the wall, green light, fed through a water meter](../../images/screenshots/inlet-filtered.jpg)

## 6. Water filter

Pond and river water is not clean. Recipe **Make Water Filter**: 2 charcoal and 2 ripped sheets give a **water filter
cartridge**. It cleans about **500 L**; its condition shows what is left.

The filter goes in the **house water inlet**: right-click it, **Fit Water Filter**, **Replace Water Filter** or
**Remove Water Filter**. A cartridge taken out keeps its wear. A worn-out one comes back as a **Spent Water Filter Cartridge**: recharge it with 2 charcoal and 1 ripped sheet (recipe **Recharge Water Filter Cartridge**), or dismantle it for its cloth. The inlet shows the
filter canister under its box. It cleans only the water that enters the house: sprinklers, drip lines and fill fittings
take the network's water as it is and never wear the cartridge.

## 7. Sprinklers

**Manual sprinkler.** Recipe **Build Sprinkler**: 2 water pipes, 1 scrap metal, 1 plank, with a pipe wrench (kept).
Set it down like furniture and feed it with a pipe. Right-click: **Open the Valve**. Its lever shows the state at a
glance: along the pipe when open, across it when closed. While its valve is open it sprays
**10 L every 10 minutes**, whether the plants are thirsty or not. The living plants in the
**5 × 5 square** around it (2 squares on each side; the sandbox option changes that reach) that are not yet at 100/100
are filled by 200 ml doses of it, nearest first; the rest is lost. A plant fills up to **100/100**, as with the
watering can (or to its own maximum when the crop sets one): at 70/100 it keeps filling instead of stopping. Any water
does, clean or not. Close it once the garden is watered: left open, it
keeps emptying your barrel or running your pump.

To see which squares are watered, right-click a sprinkler or a drip line: **Show All Watered Areas** lights up in blue
the floor of every square watered by the sprinklers and drip lines within 25 squares of you; **Hide the Watered Area**
turns it off; only one of the two is offered at a time. Their
**Information** gives their flow: how many litres they use every 10 minutes (and, for a sprinkler, how many reach the
plants).

A watering sprinkler shows an animated water jet that turns all the way round (mod option *Animated sprinkler jet*:
untick it for a still jet on slow computers). A quarter of its water is lost in the air: of 10 L, 7.5 L can reach the
plants. One water pump (50 L every 10 minutes) feeds up to five open sprinklers in full; the next ones get what is
left, then nothing. It is not silent either: you hear it water, and **zombies hear it** every 10 minutes
while it sprays. For a quiet garden that saves water, use [drip lines](#8-drip-lines).

**Automatic sprinkler.** Recipe **Add a Timer to a Sprinkler** (Electrical 2): 1 sprinkler, 2 electronics scrap,
1 electric wire, with a screwdriver (kept); 10 Electrical XP. It opens on its own **every 6 hours** and sprays for
**30 minutes** (10 L every 10 minutes), then closes. Change the interval from its right-click menu, **Watering Timer**, 1 to 24 hours (limits in the sandbox
options). The timer needs a little power (5 W: generator, grid or LiveWire); without power it does nothing, but you
can still open the valve by hand. A green light on the timer is on while the sprinkler waters.

![A sprinkler watering, jet visible (manual sprinkler shown; the automatic one sprays the same way)](../../images/screenshots/sprinkler-jet.jpg)

## 8. Drip lines

A drip line is a thin brown hose laid on the ground between your rows. It waters the plants right beside it, quietly,
without wasting water.

**Make it.** Recipe **Make Drip Lines** (Farming): 1 rubber hose and 2 uses of duct tape, with a sharp knife (kept),
give **4 drip lines**. One drip line covers one square.

**Set it down** like a pipe: right-click it in your inventory, **Place**, one per square. Drip lines join each other and
the water pipes and change shape on their own. Pick one up by hand, no tool needed.

**What it waters.** Every 10 minutes, each square of the line takes **0.5 L** from the network and waters the squares
next to it that are not part of the line, 200 ml per dose. A straight line waters the squares on both sides; the
square under the hose itself is not watered. So lay the line in a path between two rows of crops. Nothing is lost in
the air; what the plants do not need soaks away. It drips whenever the network gives it water: put a
[valve](#4-valves) before it to stop it. A drip line at the far end of a network that ran out of
pressure stays dry.

**What it needs.**

- **Any water.** Clean or not, no filter needed. Gasoline or any other fluid is refused.
- **Little pressure.** All the drip lines of a network count as **1** together, whatever their number.
- **A pump.** Like every outlet, a drip line gets water only from a [water pump](#2-build-the-water-pump) on its network.
  A network without a pump gives it nothing.

A drip line makes no sound.

## 9. Fill Fitting

Recipe **Build Fill Fitting**: 1 water pipe, 1 rubber hose, with a pipe wrench (kept). Set it down between the end
of a pipe and a barrel, a rain collector, a water cooler or a feeding trough, or in the middle of a run of pipes, where
it passes the water from one pipe to the next. Its look follows the pipes around it (straight, bent, tee or cross); the
container, when there is one, stays behind it. Right-click it: **Information** shows what it is doing.

The fill fitting only **fills**. The network fills the container beside it, up to 50 L every 10 minutes, and never above
its capacity. The water goes in **tainted**, even from a well: the pipes carry untreated water, only the house inlet
gives clean water. Animals can drink it (checked in the game's code, not yet tested in game).

A feeding trough that holds feed has no water tank (a rule of the game): the fitting gives it nothing, and its
Information says *The trough holds feed*. Filling resumes once the feed is gone. A long trough (2 to 4 squares) takes
its water in its tank, and the fitting may stand against any of its tiles.

The fitting gives water to the network only if a pump puts it there: a fill fitting never sends the water of a
container out. To send the water of a barrel into the pipes, set a [water pump](#2-build-the-water-pump) against it.

Its Information says what it is doing: filling the barrel, the barrel full (or none), no barrel next to it, another
fluid in the barrel, or *The trough holds feed*.

![Two fill fittings on vanilla rain collectors: a round barrel between two pipes (tee) and a crate where three pipes meet (cross)](../../images/screenshots/barrel-fittings.jpg)

## 10. City water

While the city water still runs, right-click a sink, bathtub, shower, toilet or washing machine that **you set down**
inside a room of a building of the map: **Connect to the City Water**. It then works like the original fixtures:
unlimited water until the city water is cut off.

The game's own **Plumb** option does something else: the fixture then draws from a tank on the floor above, not from
the city water. If you plumbed it by mistake and it stays dry, **Connect to the City Water** is still there.

## 11. Water meter

Recipe **Build Water Meter**: 1 water pipe, 1 small metal sheet, 2 screws, with a screwdriver (kept). Set it down
inline on a pipe; it follows the pipe's direction and joins only the two pipes on its axis. **Information** opens a
meter window in the style of a US water meter: a roller counter with the litres that went through it since it was set
down (kept when you pick it up and set it down again; there is no reset), a sweep hand (one turn every 10 litres), the
litres of the last 10 minutes, and the fluid (clean water or unfiltered water).

![The water meter window: rollers, sweep hand, total and last minutes](../../images/screenshots/meter-window-en.jpg)

## 12. Wells

The same water pump set down next to a **well** draws **clean water**: the house gets it without a filter. Its
Information says *Source: well (clean water)*.

Two things of the game count as a well: the **stone well** and the **metal hand pump**.

> Screenshot to do: a water pump next to a well.

## 13. Dismantle a part

Every LiveWater part can be dismantled in your inventory, with a recipe **Dismantle ...** (crafting window, Assembly
or Electrical): a pipe wrench or a wrench for the plumbing parts (pipe, valve, water meter, house inlet, sprinkler,
fill fitting), a screwdriver for the water pump and the automatic sprinkler, a knife for a drip line or a water
filter. You never get back more than the part cost, and only scrap: iron pieces, scrap metal, screws, electronics
scrap, wire. A water filter, new or spent, gives back a piece of cloth, a drip line a rubber band.

A part set down can also be dismantled where it stands, with the game's own **Disassemble** menu and the same tool
(Maintenance raises your chance for the plumbing parts, Electrical for the pump and the automatic sprinkler). It leaves
the network as if you had picked it up. A drip line is picked up by hand, then dismantled in the inventory.

### Experience

Metal parts train **Welding**, the pump and the automatic sprinkler train **Electrical**:

| Recipe | Making | Dismantling |
|---|---|---|
| Cut Pipe Sections, shut-off valve, fill fitting | 5 Welding | 2 Welding |
| Water meter, sprinkler | 8 Welding | 2 Welding |
| House water inlet | 10 Welding | 2 Welding |
| Water pump | 15 Electrical | 5 Electrical |
| Automatic sprinkler | 10 Electrical | 3 Electrical |
| Water filter cartridge, drip lines | none | none |

## 14. Finding parts

Some parts can be found instead of built, rarely: water pipes, shut-off valves and fill fittings in plumbing supplies
and tool crates, sprinklers, drip lines and water filters in garden stores and farming supplies. The water pump, the
house inlet, the water meter and the automatic sprinkler are never found: you build them.

Next: [Player base](02-player-base.md) · [Diagnostics](03-diagnostics.md)
