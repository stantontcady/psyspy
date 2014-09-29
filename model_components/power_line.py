from itertools import count

from model_components import impedance_admittance_wrangler

class PowerLine(object):
    _power_line_ids = count(0)
    
    def __init__(self, bus_a=None, bus_b=None, z=(), y=()):
        self._power_line_id = self._power_line_ids.next() + 1
        
        self.y = impedance_admittance_wrangler(z, y)
            
        self.bus_a = bus_a
        self.bus_b = bus_b
        
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])
        
    def repr_helper(self, simple=False, indent_level_increment=2):
        
        object_info = ['<Power Line #%i>' % (self._power_line_id)]
        parameters = []
        
        parameters.append('Conductance: %0.3f' % (self.y[0]))
        parameters.append('Susceptance: %0.3f' % (self.y[1]))
        
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
        