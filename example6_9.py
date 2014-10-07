#!/usr/bin/env python

from model_components import Bus, ConstantPowerLoad, PowerLine, PowerNetwork, PVBus, SynchronousDGR
from IPython import embed

l2 = ConstantPowerLoad(P=-8, Q=-2.8)

b1 = PVBus(P=1, V=1, theta0=0)
b2 = Bus(nodes=l2, shunt_y=(0, 0.5*1.72 + 0.5*0.88))
b3 = PVBus(P=5.2-0.8, V=1.05)
b4 = Bus(shunt_y=(0, 0.5*1.72 + 0.5*0.44))
b5 = Bus(shunt_y=(0, 0.5*0.88 + 0.5*0.44))

n = PowerNetwork(buses=[b1, b2, b3, b4, b5])

n.set_slack_bus(b1)

line1 = n.connect_buses(b1, b5, z=(0.0015, 0.02))
line2 = n.connect_buses(b2, b5, z=(0.0045, 0.05))
line3 = n.connect_buses(b2, b4, z=(0.0090, 0.1))
line4 = n.connect_buses(b3, b4, z=(0.00075, 0.01))
line5 = n.connect_buses(b4, b5, z=(0.00225, 0.025))


G, B, _ = n.generate_admittance_matrix()


embed()
