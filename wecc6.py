#!/usr/bin/env python

from model_components import Bus, ConstantPowerLoad, PowerNetwork, PVBus
from IPython import embed


b1 = PVBus(P=0.716, V=1, theta0=0, shunt_y=(0, 0.088 + 0.079))
b2 = PVBus(P=1.63, V=1, shunt_y=(0, 0.153 + 0.0745))
b3 = PVBus(P=0.85, V=1, shunt_y=(0, 0.1045 + 0.179))
b4 = PVBus(P=-1, V=1, shunt_y=(0, 0.0745 + 0.1045))
b5 = PVBus(P=-1.25, V=1, shunt_y=(0, 0.088 + 0.153))
b6 = PVBus(P=-0.9, V=1, shunt_y=(0, 0.079 + 0.179))

n = PowerNetwork(buses=[b1, b2, b3, b4, b5, b6])

line1 = n.connect_buses(b1, b5, z=(0, 0.1426))
line2 = n.connect_buses(b1, b6, z=(0, 0.1496))
line3 = n.connect_buses(b2, b5, z=(0, 0.2235))
line4 = n.connect_buses(b2, b4, z=(0, 0.1345))
line5 = n.connect_buses(b3, b6, z=(0, 0.2286))
line6 = n.connect_buses(b3, b4, z=(0, 0.1594))

n.set_slack_bus(b1)
_, _ = n.save_admittance_matrix()
# x = n.solve_power_flow()
# savetxt("final_states_optimal.csv", x, delimiter=",")
embed()