from itertools import count
from load import Load


class PassiveLoad(Load):
    _passive_load_ids = count(0)

    def __init__(self, R=None, L=None, C=None, V0=None, theta0=None):
        super(Load, self).__init__(V0, theta0)
        
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
        
    def __repr__(self, simple=False, base_indent=0):
        indent_level_increment = 2
        
        object_info = []
        current_states = []
        parameters = []
        
        if simple is False:
            current_states.append('Voltage magnitude, V: %0.3f pu' % (self.V[-1]))
            current_states.append('Voltage angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), self.theta[-1]))
            
        parameters.append('R: %0.3f, L: %0.3f, C: %0.3f' % (self.R, self.L, self.C))
            
        object_info.append('<Passive Load #%i>' % (self._passive_load_id))
        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
            
        return '\n'.join(['%s%s' % ((''.rjust(base_indent), line)) for line in object_info])