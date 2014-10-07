#!/usr/bin/env python

from model_components import Bus, ConstantPowerLoad, PowerLine, PowerNetwork, PVBus, SynchronousDGR
from IPython import embed


la = ConstantPowerLoad(P=1.25, Q=0.5) # Station A
lb = ConstantPowerLoad(P=0.9, Q=0.3) # Station B
lc = ConstantPowerLoad(P=1, Q=0.35) # Station C

b1 = PVBus(P=0.716, Q=0.27, V=1.04, theta0=0)
b2 = PVBus(P=1.63, Q=0.067, V=1.025, theta0=0.16231562)
b3 = PVBus(P=0.85, Q=-0.109, V=1.025, theta0=0.08203048)
b4 = Bus(V0=1.026, theta0=-0.0383972435, shunt_y=(0, 0.5*0.176 + 0.5*0.158))
b5 = Bus(nodes=la, V0=0.996, theta0=-0.0698131701, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
b6 = Bus(nodes=lb, V0=1.013, theta0=-0.0645771823, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
b7 = Bus(V0=1.026, theta0=0.0645771823, shunt_y=(0, 0.5*0.306 + 0.5*0.149))
b8 = Bus(nodes=lc, V0=1.016, theta0=0.0122173048, shunt_y=(0, 0.5*0.149 + 0.5*0.209))
b9 = Bus(V0=1.032, theta0=0.034906585, shunt_y=(0, 0.5*0.358 + 0.5*0.209))

n = PowerNetwork(buses=[b1, b2, b3, b4, b5, b6, b7, b8, b9])

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

# bus 2 = bus 7
# bus 3 = bus 9
# bus 1 = bus 4
