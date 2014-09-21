from itertools import count


class PowerLine(object):
    _power_line_ids = count(0)
    
    def __init__(self, bus_a=None, bus_b=None, r=None, x=None, g=None, b=None):
        self._power_line_id = self._power_line_ids.next() + 1
        
        if r is not None and g is not None and round((1./r), 5) != round(g):
            print 'Resistance and conductance provided without different values, using resistance.'
            self.g = 1./r
        elif r is not None and g is None:
            self.g = 1./r
        elif r is None and g is not None:
            self.g = g
        else:
            print 'No resistance or conductance provided, assuming lossless line.'
            self.g = 0
        
        if x is not None and b is not None and round((1./x), 5) != round(b):
            print 'Reactance and susceptance provided without different values, using reactance.'
            self.g = 1./r
        elif x is not None and b is None:
            self.b = 1./x
        elif x is None and b is not None:
            self.b = b
        else:
            print 'No reactance or susceptance provided, assuming zero-value; this may result in unexpected behavior.'
            self.b = 0
            
        self.bus_a = bus_a
        self.bus_b = bus_b
        
    def __repr__(self, base_indent=0):
        indent_level_increment = 2
        
        object_info = []
        parameters = []
        
        parameters.append('Conductance: %0.2f' % (self.g))
        parameters.append('Susceptance: %0.2f' % (self.b))
        
        
        object_info.append('<Power Line #%i>' % (self._power_line_id))
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])

        object_info.append('%sConnected buses:\n' % (''.rjust(indent_level_increment)))

        object_info = '\n'.join(['%s%s' % ((''.rjust(base_indent), line)) for line in object_info])
        
        object_info += self.bus_a.__repr__(base_indent=4) + '\n' # simple=True, base_indent=4
        object_info += self.bus_b.__repr__(base_indent=4) # simple=True, base_indent=4
        
        return object_info

    def get_id(self):
        return self.power_line_id
        