from itertools import count

from numpy import array, append

from model_components import set_initial_conditions


class Node(object):
    _node_ids = count(0)
    
    def __init__(self, V0=None, theta0=None):
        self._node_id = self._node_ids.next() + 1
        self.set_initial_node_voltage(V0, theta0)
        
    def __repr__(self):
        pass
        
    def set_initial_node_voltage(self, V0=None, theta0=None):
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
        return self.get_current_node_voltage()
        
        
    def update_node_voltage(self, V, theta):
        self.V = append(self.V, V)
        self.theta = append(self.theta, theta)
        return self.get_current_node_voltage()
        
        
    def get_current_node_voltage(self):
        return array([self.V[-1], self.theta[-1]])
        
    def get_id(self):
        return self._node_id