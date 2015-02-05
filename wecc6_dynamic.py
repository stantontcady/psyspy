#!/usr/bin/env python
from logging import getLogger
from math import pi

from IPython import embed
from matplotlib.pylab import plot, figure, show, ylim
from numpy import amax, amin


from microgrid_model import Bus, PowerNetwork, ConstantApparentPowerModel, KuramotoOscillatorLoadModel as KuramotoLoad
from microgrid_model import KuramotoOscillatorGeneratorModel as KuramotoGenerator
from microgrid_model import SimulationRoutine, KuramotoOscillatorLoadModelRealPowerSetpointPerturbation as KuramotoLoadPerturbation

logger = getLogger()
logger.setLevel(10)

g1 = KuramotoGenerator(
    parameters={'D': 0.125},
    initial_setpoint=0.67
)

g2 = KuramotoGenerator(
    parameters={'D': 0.0679},
    initial_setpoint=1.63
)

g3 = KuramotoGenerator(
    parameters={'D': 0.0479},
    initial_setpoint=0.85
)

l1 = KuramotoLoad(
    parameters={'D': 0.0125},
    initial_load=1.0
)

l2 = KuramotoLoad(
    parameters={'D': 0.00679},
    initial_load=1.25
)

l3 = KuramotoLoad(
    parameters={'D': 0.00479},
    initial_load=0.9
)

b1 = Bus(model=g1, V0=1, shunt_y=(0, 0.088 + 0.079))
b2 = Bus(model=g2, V0=1, shunt_y=(0, 0.153 + 0.0745))
b3 = Bus(model=g3, V0=1, shunt_y=(0, 0.1045 + 0.179))
b4 = Bus(model=l1, V0=1, shunt_y=(0, 0.0745 + 0.1045))
b5 = Bus(model=l2, V0=1, shunt_y=(0, 0.088 + 0.153))
b6 = Bus(model=l3, V0=1, shunt_y=(0, 0.079 + 0.179))

n = PowerNetwork(buses=[b1, b2, b3, b4, b5, b6])

line1 = n.connect_buses(b1, b5, z=(0, 0.1426))
line2 = n.connect_buses(b1, b6, z=(0, 0.1496))
line3 = n.connect_buses(b2, b5, z=(0, 0.2235))
line4 = n.connect_buses(b2, b4, z=(0, 0.1345))
line5 = n.connect_buses(b3, b6, z=(0, 0.2286))
line6 = n.connect_buses(b3, b4, z=(0, 0.1594))

n.set_slack_bus(b1)
p1 = KuramotoLoadPerturbation(affected_model=l3, new_load=1.1, start_time=0.1, end_time=0.2)
p2 = KuramotoLoadPerturbation(affected_model=l2, new_load=1, start_time=0.5, end_time=0.6)

sim = SimulationRoutine(n, 1, perturbations=[p1, p2], time_step=0.001)
sim.run_simulation()
t = sim.time_vector

figure(1)
for bus in n.buses:
    plot(t, bus.model.d[0:(bus.model.d.shape[0]-1)])

# figure(2)
# for bus in n.buses:
#     plot(t, bus.theta[0:(bus.theta.shape[0]-1)])

embed()
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
