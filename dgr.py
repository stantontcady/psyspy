from itertools import count
from math import pi
from numpy import empty, append

from helper_functions import set_initial_conditions
from node import Node


class DGR(Node):
    _dgr_ids = count(0)

    def __init__(self, V0=None, theta0=None):
        super(Node, self).__init__(V0, theta0)
        
        self.drg_id = self._dgr_ids.next() + 1