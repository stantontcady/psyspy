from itertools import count

from numpy import append

from ..bus import Bus
from model_components import set_initial_conditions


class PVBus(Bus):
    _pv_bus_ids = count(0)
    
    def __init__(self, P=None, V=None, theta0=None, shunt_z=(), shunt_y=()):
        Bus.__init__(self, None, V, theta0, shunt_z, shunt_y)
        
        self._pv_bus_id = self._pv_bus_ids.next() + 1
        
        set_initial_conditions(self, 'P', P)
        set_initial_conditions(self, 'Q')
        
        self._node_type = 'pv_bus'

            
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])


    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<PV Bus, Node #%i>' % (self.get_id())]
        
        current_states = []
        V, theta = self.get_current_node_voltage()
        current_states.append('Magnitude, V: %0.3f pu' % (V))
        current_states.append('Angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), theta))
        
        if current_states != []:
            object_info.append('%sCurrent voltage:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        
        if self.shunt_y != (0, 0):
            object_info.append('%sShunt admittance:' % (''.rjust(indent_level_increment)))
            if self.shunt_y[0] != 0:
                object_info.append('%sConductance: %0.3f' % (''.rjust(2*indent_level_increment), self.shunt_y[0]))
            if self.shunt_y[1] != 0:
                object_info.append('%sSusceptance: %0.3f' % (''.rjust(2*indent_level_increment), self.shunt_y[1]))
        
        if self.child_nodes != []:    
            object_info.append('%sConnected nodes:' % (''.rjust(indent_level_increment)))
        else:
            object_info.append('%sNo nodes connected!' % (''.rjust(indent_level_increment)))
        
        for node in self.child_nodes:
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), line)
                                for line in node.repr_helper(simple=True, indent_level_increment=indent_level_increment)])
        
        return object_info


    def get_pv_bus_id(self):
        return self._pv_bus_id

        
    def update_node_voltage(self, V, theta):
        # special function to update voltage while maintaining voltage magnitude since this is a PV bus
        self.V = append(self.V, self.V[-1])
        self.theta = append(self.theta, theta)
        return self.get_current_node_voltage()

        
    def update_real_reactive_power(self, P, Q):
        self.P = append(self.P, self.P[-1])
        self.Q = append(self.Q, Q)
        return self.get_current_real_reactive_power()


    def get_current_real_reactive_power(self):
        return self.P[-1], self.Q[-1]