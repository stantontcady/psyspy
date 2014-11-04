from itertools import count

from numpy import append

from model_components import impedance_admittance_wrangler, set_initial_conditions


class PowerLine(object):
    _power_line_ids = count(0)
    
    def __init__(self, bus_a=None, bus_b=None, z=(), y=()):
        self._power_line_id = self._power_line_ids.next() + 1
        
        self.y = impedance_admittance_wrangler(z, y)
            
        self.bus_a = bus_a
        self.bus_b = bus_b
        
        set_initial_conditions(self, 'Pab', 0)
        set_initial_conditions(self, 'Qab', 0)
        
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])
        
    def repr_helper(self, simple=False, indent_level_increment=2):
        
        object_info = ['<Power Line #%i>' % (self._power_line_id)]
        
        current_states = []
        P, Q = self.get_current_complex_power()
        current_states.append('Real power, P: %0.3f pu' % (P))
        current_states.append('Reactive power, Q: %0.3f pu' % (Q))
        
        parameters = []
        
        parameters.append('Conductance: %0.3f' % (self.y[0]))
        parameters.append('Susceptance: %0.3f' % (self.y[1]))
        
        if current_states != []:
            object_info.append('%sComplex power from node %s to %s:' % (''.rjust(indent_level_increment),
                                                                        self.bus_a.get_id(),
                                                                        self.bus_b.get_id()))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), current_state) for current_state in current_states])
        
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
        
        if simple is False:
            object_info.append('%sBuses to which this line is incident:' % (''.rjust(indent_level_increment)))
        
            for bus in [self.bus_a, self.bus_b]:
                object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), bus_info)
                                    for bus_info in bus.repr_helper(simple=True,
                                                                    indent_level_increment=indent_level_increment)])

        return object_info

    def get_id(self):
        return self._power_line_id
        
    
    def get_incident_buses(self):
        if self.bus_a is None or self.bus_b is None:
            raise AttributeError('missing an incident bus, make sure power line is connected to two buses')
        
        return self.bus_a, self.bus_b
        
        
    def append_complex_power(self, P, Q):
        Pout = self.append_real_power(P)
        Qout = self.append_reactive_power(Q)
        return Pout, Qout

        
    def append_real_power(self, P):
        self.Pab = append(self.Pab, P)
        return self.get_current_real_power()

        
    def append_reactive_power(self, Q):
        self.Qab = append(self.Qab, Q)
        return self.get_current_reactive_power()
        
    
    def replace_complex_power(self, P, Q):
        Pout = self.replace_real_power(P)
        Qout = self.replace_reactive_power(Q)
        return Pout, Qout

    
    def replace_real_power(self, P):
        self.Pab[-1] = P
        return self.get_current_real_power()
        
    
    def replace_reactive_power(self, Q):
        self.Qab[-1] = Q
        return self.get_current_reactive_power()

        
    def get_current_complex_power(self):
        return self.get_current_real_power(), self.get_current_reactive_power()


    def get_current_real_power(self):
        return self.Pab[-1]
        

    def get_current_reactive_power(self):
        return self.Qab[-1]
