#!/usr/bin/env python

from model_components import Bus, PassiveLoad, PowerLine, PowerNetwork, SynchronousDGR
from IPython import embed

g1 = SynchronousDGR()
g2 = SynchronousDGR()
g3 = SynchronousDGR()

l1 = PassiveLoad(R=5)

b1 = Bus(nodes=g1)
b2 = Bus(nodes=g3)
b3 = Bus(nodes=l1)
b4 = Bus(nodes=g2)

n = PowerNetwork(buses=[b1,b2])
n.connect_buses(b1, b2, r=0.1, b=0.25)

line1 = PowerLine(b2, b3, r=0.05, b=0.1)
n.add_power_line(line1)

n.connect_buses(b1, b4, r=0.15, b=0.05)
n.connect_buses(b3, b4, r=0.15, b=0.05)

embed()