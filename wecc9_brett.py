#!/usr/bin/env python

from model_components import Bus, ConstantPowerLoad, PowerLine, PowerNetwork, PVBus, SynchronousDGR
from IPython import embed
from math import radians

la = ConstantPowerLoad(P=1.25, Q=0.5) # Station A
lb = ConstantPowerLoad(P=0.9, Q=0.3) # Station B
lc = ConstantPowerLoad(P=1, Q=0.35) # Station C

# b1 = PVBus(P=0.716, V=1.04, theta0=0)
# b2 = PVBus(P=1.63, V=1.025)
# b3 = PVBus(P=0.85, V=1.025)
# b5 = Bus(nodes=la, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
# b6 = Bus(nodes=lb, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
# b8 = Bus(nodes=lc, shunt_y=(0, 0.5*0.149 + 0.5*0.209))

b1 = PVBus(P=0.716, V=1.04, theta0=0)
b2 = PVBus(P=1.63, V=1.025)
b3 = PVBus(P=0.85, V=1.025)
b4 = Bus(shunt_y=(0, 0.5*0.176 + 0.5*0.158))
b5 = Bus(nodes=la, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
b6 = Bus(nodes=lb, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
b7 = Bus(shunt_y=(0, 0.5*0.306 + 0.5*0.149))
b8 = Bus(nodes=lc, shunt_y=(0, 0.5*0.149 + 0.5*0.209))
b9 = Bus(shunt_y=(0, 0.5*0.358 + 0.5*0.209))

# b1 = PVBus(P=0.716, V=1.04, theta0=0)
# b2 = PVBus(P=1.63, V=1.025, theta0=radians(9.28))
# b3 = PVBus(P=0.85, V=1.025, theta0=radians(4.66475))
# b4 = Bus(shunt_y=(0, 0.5*0.176 + 0.5*0.158), V0=1.025788, theta0=radians(-2.21678))
# b5 = Bus(nodes=la, shunt_y=(0, 0.5*0.176 + 0.5*0.306), V0=0.9956, theta0=radians(-3.9888))
# b6 = Bus(nodes=lb, shunt_y=(0, 0.5*0.158 + 0.5*0.358), V0=1.01265, theta0=radians(-3.6873))
# b7 = Bus(shunt_y=(0, 0.5*0.306 + 0.5*0.149), V0=1.025769, theta0=radians(3.7197))
# b8 = Bus(nodes=lc, shunt_y=(0, 0.5*0.149 + 0.5*0.209), V0=1.01588, theta0=radians(0.727536))
# b9 = Bus(shunt_y=(0, 0.5*0.358 + 0.5*0.209), V0=1.03235, theta0=radians(1.9667))

# n = PowerNetwork(buses=[b1, b2, b3, b5, b6, b8])
n = PowerNetwork(buses=[b1, b2, b3, b4, b5, b6, b7, b8, b9])

# line1 = n.connect_buses(b1, b5, z=(0, 0.0576))
# line5 = n.connect_buses(b1, b6, z=(0.017, 0.092))
# line6 = n.connect_buses(b2, b5, z=(0.032, 0.161))
# line2 = n.connect_buses(b2, b8, z=(0, 0.0625))
# line3 = n.connect_buses(b3, b6, z=(0, 0.0586))
# line9 = n.connect_buses(b3, b8, z=(0.0119, 0.1008))


line1 = n.connect_buses(b1, b4, z=(0, 0.0576))
line4 = n.connect_buses(b4, b5, z=(0.01, 0.085))
line6 = n.connect_buses(b5, b7, z=(0.032, 0.161))
line5 = n.connect_buses(b4, b6, z=(0.017, 0.092))
line7 = n.connect_buses(b6, b9, z=(0.039, 0.17))
line8 = n.connect_buses(b7, b8, z=(0.0085, 0.072))
line3 = n.connect_buses(b3, b9, z=(0, 0.0586))
line9 = n.connect_buses(b8, b9, z=(0.0119, 0.1008))
line2 = n.connect_buses(b2, b7, z=(0, 0.0625))


n.set_slack_bus(b1)

G, B, _ = n.generate_admittance_matrix()

embed()