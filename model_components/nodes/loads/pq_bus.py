from itertools import count

from numpy import append

from ..bus import Bus
from constant_power_load import ConstantPowerLoad
from model_components import set_initial_conditions


class PQBus(Bus):
    _pq_bus_ids = count(0)
    
    def __init__(self, P=None, Q=None, V0=None, theta0=None, shunt_z=(), shunt_y=()):
        
        load = ConstantPowerLoad(P=P, Q=Q, V0=V0, theta0=theta0)
        
        Bus.__init__(self, dgr=None, loads=load, V0=V0, theta0=theta0, shunt_z=shunt_z, shunt_y=shunt_y)
        
        self._pq_bus_id = self._pq_bus_ids.next() + 1
        
        self._node_type = 'pq_bus'

            
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])


    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<PQ Bus, Node #%i>' % (self.get_id())]
        
        current_states = []
        V, theta = self.get_current_voltage()
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
        
        return object_info

        
    def change_real_and_reactive_power(self, P, Q):
        return self.loads[0].change_real_and_reactive_power(P, Q)


    def get_current_real_reactive_power(self):
        return self.loads[0].get_real_and_reactive_power()
