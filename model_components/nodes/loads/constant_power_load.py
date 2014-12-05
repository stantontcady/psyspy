from itertools import count

from load import Load


class ConstantPowerLoad(Load):
    _constant_power_load_ids = count(0)

    def __init__(self, P=None, Q=None, V0=None, theta0=None):
        Load.__init__(self, V0, theta0)
        
        self._constant_power_load_id = self._constant_power_load_ids.next() + 1
        
        if P is None:
            P = 0
        self.P = P
        
        if Q is None:
            Q = 0
        self.Q = Q
        
        self._node_type = 'constant_power_load'

        
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])

        
    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<Constant Power Load #%i>' % (self._constant_power_load_id)]
        current_states = []
        parameters = []
        
        if simple is False:
            V, theta = self.get_current_voltage()
            current_states.append('Voltage magnitude, V: %0.3f pu' % (V))
            current_states.append('Voltage angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), theta))
            
        parameters.append('P: %0.3f, Q: %0.3f' % (self.P, self.Q))

        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        if parameters != []:
            object_info.append('%sReal and Reactive Power Values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
            
        return object_info

    
    def get_real_and_reactive_power(self):
        return self.get_real_power(), self.get_real_power()
        
    
    def change_real_and_reactive_power(self, new_P, new_Q):
        P = self.change_real_power(new_P)
        Q = self.change_reactive_power(new_Q)
        return P, Q


    def get_real_power(self):
        return self.P
        

    def change_real_power(self, new_P):
        self.P = new_P
        return self.get_real_power()
    
    
    def get_reactive_power(self):
        return self.Q
        

    def change_reactive_power(self, new_Q):
        self.Q = new_Q
        return self.get_reactive_power()
