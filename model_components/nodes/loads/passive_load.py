from itertools import count

from load import Load


class PassiveLoad(Load):
    _passive_load_ids = count(0)

    def __init__(self, R=None, L=None, C=None, V0=None, theta0=None):
        Load.__init__(self, V0, theta0)
        
        self._passive_load_id = self._passive_load_ids.next() + 1
        
        if R is None:
            R = 0
        self.R = R
        
        if L is None:
            L = 0
        self.L = L
        
        if C is None:
            C = 0
        self.C = C
        
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])
        
    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<Passive Load #%i>' % (self._passive_load_id)]
        current_states = []
        parameters = []
        
        if simple is False:
            V, theta = self.get_current_node_voltage()
            current_states.append('Voltage magnitude, V: %0.3f pu' % (V))
            current_states.append('Voltage angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), theta))
            
        parameters.append('R: %0.3f, L: %0.3f, C: %0.3f' % (self.R, self.L, self.C))

        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
            
        return object_info