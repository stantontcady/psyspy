#!/usr/bin/env python

from IPython import embed

from model_components import Bus, ConstantPowerLoad, PVBus
from simulation_resources import TemporaryConstantPowerLoadChange

l = ConstantPowerLoad(P=1.25, Q=0.5)
b = Bus(nodes=l, shunt_y=(0, 0.5*0.176 + 0.5*0.306))

embed()