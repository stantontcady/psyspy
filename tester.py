#!/usr/bin/env python
from math import pi

from model_components import SynchronousDGR
from IPython import embed

dgr = SynchronousDGR(
    V0=1.04,
    theta0=0,
    parameters={'wnom': 2*pi*59.5, 'M': 1./(pi*59.5), 'E': 1},
    initial_states={'u0': 0.7}
)

embed()