#!/usr/bin/env python

from model_components import Bus, ConstantPowerLoad, PowerLine, PowerNetwork, SynchronousDGR
from IPython import embed


g1 = SynchronousDGR() # slack bus
g2 = SynchronousDGR() # gen 2
g3 = SynchronousDGR() # gen 3

la = ConstantPowerLoad(P=125e6, Q=50e6) # Station A
lb = ConstantPowerLoad(P=90e6, Q=30e6) # Station B
lc = ConstantPowerLoad(P=100e6, Q=35e6) # Station C

b1 = Bus(nodes=g1)
b2 = Bus(nodes=g2)
b3 = Bus(nodes=g3)
b4 = Bus(shunt_y=(0, 0.088+0.079))
b5 = Bus(nodes=la, shunt_y=(0, 0.088+0.153))
b6 = Bus(nodes=lb, shunt_y=(0, 0.079+0.179))
b7 = Bus(shunt_y=(0, 0.153+0.0745))
b8 = Bus(nodes=lc, shunt_y=(0, 0.0745+0.1045))
b9 = Bus(shunt_y=(0, 0.1045+0.179))

n = PowerNetwork(buses=[b1, b2, b3, b4, b5, b6, b7, b8, b9])

line1 = n.connect_buses(b1, b4, z=(0, 0.0576))
line2 = n.connect_buses(b2, b7, z=(0, 0.0625))
line3 = n.connect_buses(b3, b9, z=(0, 0.0586))
line4 = n.connect_buses(b4, b5, z=(0.01, 0.085))
line5 = n.connect_buses(b4, b6, z=(0.017, 0.092))
line6 = n.connect_buses(b5, b7, z=(0.032, 0.161))
line7 = n.connect_buses(b6, b9, z=(0.039, 0.17))
line8 = n.connect_buses(b7, b8, z=(0.0085, 0.072))
line9 = n.connect_buses(b8, b9, z=(0.0119, 0.1008))

G, B = n.generate_admittance_matrix()

embed()

# bus 2 = bus 7
# bus 3 = bus 9
# bus 1 = bus 4
