#!/usr/bin/env python
from math import pi

from model_components import SynchronousDGR
from IPython import embed

dgr = SynchronousDGR(
    V0=1.04,
    theta0=0,
    initial_states={'u0': 0.716, 'd0': 0, 'w0': 2*pi*59.5, 'P0': 0.7, 'E0': 1, 'M': 1/(pi*59.5)}
)

embed()