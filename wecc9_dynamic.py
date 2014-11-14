#!/usr/bin/env python

from model_components import Bus, ConstantPowerLoad, PowerLine, PowerNetwork, PVBus, SynchronousDGR
from IPython import embed


g1 = SynchronousDGR(
    V0=1.04,
    theta0=0,
    parameters={'H': 23.64, 'X': 0.146, 'D': 0.0125, 'E': 1},
    initial_setpoints={'u': 0.716}
)

g2 = SynchronousDGR(
    V0=1.025,
    parameters={'H': 6.4, 'X': 0.8958, 'D': 0.00679, 'E': 1},
    initial_setpoints={'u': 1.63}
)

g3 = SynchronousDGR(
    V0=1.025,
    parameters={'H': 3.01, 'X': 1.3125, 'D': 0.00479, 'E': 1},
    initial_setpoints={'u': 0.85}
)

la = ConstantPowerLoad(P=1.25, Q=0.5) # Station A
lb = ConstantPowerLoad(P=0.9, Q=0.3) # Station B
lc = ConstantPowerLoad(P=1, Q=0.35) # Station C

b1 = Bus(nodes=g1)
b2 = Bus(nodes=g2)
b3 = Bus(nodes=g3)
b4 = Bus(shunt_y=(0, 0.5*0.176 + 0.5*0.158))
b5 = Bus(nodes=la, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
b6 = Bus(nodes=lb, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
b7 = Bus(shunt_y=(0, 0.5*0.306 + 0.5*0.149))
b8 = Bus(nodes=lc, shunt_y=(0, 0.5*0.149 + 0.5*0.209))
b9 = Bus(shunt_y=(0, 0.5*0.358 + 0.5*0.209))

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

n.set_slack_bus(b1)

embed()
