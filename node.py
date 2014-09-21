from itertools import count
from numpy import empty

from helper_functions import set_initial_conditions


class Node(object):
    _node_ids = count(0)
    
    def __init__(self, V0=None, theta0=None):
        self.node_id = self._node_ids.next() + 1
        
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)