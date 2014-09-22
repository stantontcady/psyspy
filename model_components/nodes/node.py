from itertools import count

from numpy import empty, append

from model_components import set_initial_conditions


class Node(object):
    _node_ids = count(0)
    
    def __init__(self, V0=None, theta0=None):
        self._node_id = self._node_ids.next() + 1
        
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
        
    def update_node_voltage(self, V, theta):
        self.V = append(self.V, V)
        self.theta = append(self.theta, theta)