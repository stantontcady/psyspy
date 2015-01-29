#!/usr/bin/env python
from math import pi

from IPython import embed
from matplotlib.pylab import plot, figure, show, ylim
from numpy import amax, amin


from microgrid_model import Bus, PowerNetwork, ConstantApparentPowerModel
from microgrid_model.model_components.models import ConstantApparentPowerModel, StructurePreservingSynchronousGeneratorModel
from microgrid_model.simulation_resources import SimulationRoutine, TemporaryConstantPowerLoadChange, PermanentConstantPowerLoadChange, TemporaryPowerLineImpedanceChange

l1 = ConstantApparentPowerModel(P=1.25, Q=0.5)
l2 = ConstantApparentPowerModel(P=0.9, Q=0.3)
l3 = ConstantApparentPowerModel(P=1, Q=0.35)

g1 = StructurePreservingSynchronousGeneratorModel(
    parameters={'H': 23.64, 'Xdp': 0.0608, 'D': 0.0125},
    initial_setpoint=0.716
)

g2 = StructurePreservingSynchronousGeneratorModel(
    parameters={'H': 6.4, 'Xdp': 0.1198, 'D': 0.00679},
    initial_setpoint=1.63
)

g3 = StructurePreservingSynchronousGeneratorModel(
    parameters={'H': 3.01, 'Xdp': 0.1813, 'D': 0.00479},
    initial_setpoint=0.85
)

b1 = Bus(model=g1, V0=1.04, theta0=0)
b2 = Bus(model=g2, V0=1.025)
b3 = Bus(model=g3, V0=1.025)
b4 = Bus(shunt_y=(0, 0.5*0.176 + 0.5*0.158))
b5 = Bus(model=l1, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
b6 = Bus(model=l2, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
b7 = Bus(shunt_y=(0, 0.5*0.306 + 0.5*0.149))
b8 = Bus(model=l3, shunt_y=(0, 0.5*0.149 + 0.5*0.209))
b9 = Bus(shunt_y=(0, 0.5*0.358 + 0.5*0.209))

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


# c1 = TemporaryConstantPowerLoadChange(start_time=0.5, end_time=2, affected_load=b5, new_P=1.5)
# c2 = PermanentConstantPowerLoadChange(start_time=0.5, affected_load=lb, new_P=1)
c2 = TemporaryPowerLineImpedanceChange(affected_line=line4, start_time=1, end_time=1.1, new_z=(0.015, 0.085))
# c2 = TemporaryConstantPowerLoadChange(start_time=2, end_time=10, affected_node=la, new_Q=0.85)
# c2 = TemporaryConstantPowerLoadChange(start_time=1.5, end_time=10.1, affected_node=lb, new_P=1.25)


sim = SimulationRoutine(n, 10, [c2])
sim.run_simulation()
t = sim.time_vector


figure(1)
for bus in n.buses:
    plot(t, bus.theta)
    
show()

# w1 = g1.w[0:(g1.w.shape[0]-1)]
# w2 = g2.w[0:(g2.w.shape[0]-1)]
# w3 = g3.w[0:(g3.w.shape[0]-1)]
# 
# figure(1)
# plot(t, w1, t, w2, t, w3)
# ymin = min(amin(w1), amin(w2), amin(w2)) - 0.1
# ymax = max(amax(w1), amax(w2), amax(w2)) + 0.1
# ylim(ymin, ymax)
# print abs(2*pi*60-w1[-1])
# print abs(2*pi*60-w2[-1])
# print abs(2*pi*60-w3[-1])
# ylim(ymin, ymax)
# figure(2)
# plot(t, w2)
# ylim(ymin, ymax)
# figure(3)
# plot(t, w3)
# ylim(ymin, ymax)
# show()
