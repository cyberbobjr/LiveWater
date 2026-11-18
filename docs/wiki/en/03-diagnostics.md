# Diagnostics

## Network view

Right-click any part of a network (pipe, pump, inlet, sprinkler, fitting): **Show the Water Network**. The whole
network is highlighted until you choose **Hide the Water Network**:

| Colour | Meaning |
|---|---|
| green | outlets that get water |
| red | outlets without enough pressure |
| amber | outlets that refuse unfiltered water (a house inlet without a filter) |
| grey | closed, or no water in the pipes |
| blue | pipes and pumps |

The tooltip of *Hide the Water Network* counts the outlets in each state.

> Screenshot to do: a highlighted network with a green inlet and a red sprinkler.

## Information lines

**Information** in the right-click menu of a part shows what it does:

- pump: state, flow, efficiency, filter left, source (natural water or well);
- house inlet: *delivered to the house*, *the house tanks are full*, *none in the pipes*, *unfiltered*, *not enough
  pressure*, *shut off*, or *the pipes carry gasoline*;
- sprinkler: watering, nothing to water, no water, unfiltered (sprinklers accept it), no pressure, valve closed; the
  timer interval and whether it has power;
- barrel fitting: mode (Fill or Pump), litres in the barrel, and what it is doing;
- water meter: litres in the last 10 minutes and the fluid.

## Why a tap has no water

Right-click a sink, bathtub, shower, toilet or washing machine that has no water: a line **No water: ...** says why.

| Reason shown | What to do |
|---|---|
| not plumbed yet | use a pipe wrench on it (the game's Plumb action) |
| no house water inlet serves it | set an inlet on this building, or move closer (range, floors) |
| its tank belongs to something else, and it is empty | another system (a barrel above it, a LiveWire pump) feeds it |
| the water is on its way | wait up to 10 minutes |
| the pump's water is unfiltered | fit a filter, or pump from a well |
| not enough pressure | fewer outlets on that pump, or a second pump |
| no water in the pipes | the pump is off, broken down or without power |
| a valve is closed | open it |
| the barrels stand lower than this fixture | add a pump to the network, or power the barrel's square |
| the barrels are empty or hold something other than water | refill or empty them |
| the inlet has no pump and no barrel | pipe a pump to it or connect a barrel |
| the pipes carry gasoline | this network moves gasoline, not water |

> Screenshot to do: the right-click menu of a dry sink with its "No water" line.

Next: [LiveWire](04-livewire.md)
