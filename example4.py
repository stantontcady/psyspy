#!/usr/bin/env python

from model_components import Bus, ConstantPowerLoad, PowerLine, PowerNetwork, PVBus, SynchronousDGR
from IPython import embed


b1 = PVBus(P=1.02, V=1, theta0=0)
b2 = PVBus(P=1, V=1.04, theta0=0.2)
b3 = Bus(V0=1, theta0=0.1)
b4 = Bus(V0=1, theta0=0.1)
b5 = Bus(V0=1, theta0=0.1)
b6 = Bus(V0=1, theta0=0.1)
b7 = Bus(V0=1, theta0=0.1)

n = PowerNetwork(buses=[b1, b2, b3, b4, b5, b6, b7])

line1 = n.connect_buses(b1, b6, z=(0, 0.0576))
line2 = n.connect_buses(b1, b7, z=(0, 0.0625))
line3 = n.connect_buses(b2, b3, z=(0, 0.0586))
line4 = n.connect_buses(b3, b4, z=(0.01, 0.085))
line5 = n.connect_buses(b3, b5, z=(0.017, 0.092))
line6 = n.connect_buses(b4, b5, z=(0.017, 0.092))
line7 = n.connect_buses(b4, b6, z=(0.017, 0.092))
line8 = n.connect_buses(b5, b7, z=(0.017, 0.092))


# G, B = n.generate_admittance_matrix()

J = n.generate_jacobian_matrix()

embed()

# bus 2 = bus 7
# bus 3 = bus 9
# bus 1 = bus 4
