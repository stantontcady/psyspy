from itertools import count

from numpy import append, array

from model_components import set_initial_conditions
from ..node import Node
from dgr import DGR


class PVDGR(DGR):
    _pv_dgr_ids = count(0)

    def __init__(self, P, V, theta0=None):
        super(DGR, self).__init__(V, theta0)
        
        self._pv_dgr_id = self._pv_dgr_ids.next() + 1
        
        set_initial_conditions(self, 'P', P)
        set_initial_conditions(self, 'Q')
        
    
    def __repr__(self):
        return '<PVDGR>'

        
    def update_node_voltage(self, V, theta):
        print 'using PV-specific func'
        # special function to update voltage while maintaining voltage magnitude since this is a PV bus
        self.V = append(self.V, self.V[-1])
        self.theta = append(self.theta, theta)
        return self.get_current_node_voltage()


    def update_real_reactive_power(self, P, Q):
        self.P = append(self.P, self.P[-1])
        self.Q = append(self.Q, Q)
        return self.get_current_real_reactive_power()


    def get_current_real_reactive_power(self):
        return array([self.P[-1], self.Q[-1]])