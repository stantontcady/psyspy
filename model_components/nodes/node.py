from itertools import count

from numpy import array, append

from model_components import set_initial_conditions


class Node(object):
    _node_ids = count(0)
    
    def __init__(self, V0=None, theta0=None):
        self._node_id = self._node_ids.next() + 1
        
        if V0 is None:
            V0 = 1
        if theta0 is None:
            theta0 = 0

        _, _ = self.set_initial_node_voltage(V0, theta0)
        
        self._node_type = 'Node'
        
        
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])

        
    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<Node #%i>' % (self._node_id)]
        
        current_states = []
        V, theta = self.get_current_node_voltage()
        current_states.append('Magnitude, V: %0.3f pu' % (V))
        current_states.append('Angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), theta))
        
        if current_states != []:
            object_info.append('%sCurrent voltage:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
            
        return object_info

        
    def set_initial_node_voltage(self, V0=None, theta0=None):
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
        return self.get_current_node_voltage()
        
        
    def append_node_voltage(self, V, theta):
        Vout = self.append_node_voltage_magnitude(V)
        thetaOut = self.append_node_voltage_angle(theta)
        return Vout, thetaOut

        
    def append_node_voltage_magnitude(self, V):
        self.V = append(self.V, V)
        return self.get_current_node_voltage_magnitude()
        

    def append_node_voltage_angle(self, theta):
        self.theta = append(self.theta, theta)
        return self.get_current_node_voltage_angle()

        
    def replace_node_voltage(self, V, theta):
        Vout = self.replace_node_voltage_magnitude(V)
        thetaOut = self.replace_node_voltage_angle(theta)
        return Vout, thetaOut
    
    
    def replace_node_voltage_magnitude(self, V):
        self.V[-1] = V
        return self.get_current_node_voltage_magnitude()


    def replace_node_voltage_angle(self, theta):
        self.theta[-1] = theta
        return self.get_current_node_voltage_angle()
    
        
    def get_current_node_voltage(self):
        return self.get_current_node_voltage_magnitude(), self.get_current_node_voltage_angle()
       
        
    def get_current_node_voltage_magnitude(self):
        return self.V[-1]
        

    def get_current_node_voltage_angle(self):
        return self.theta[-1]
        
    
    def _voltage_helper(self, V=None, theta=None):
        if V is None:
            V = self.get_current_node_voltage_magnitude()
        if theta is None:
            theta = self.get_current_node_voltage_angle()
        return V, theta


    def get_id(self):
        return self._node_id

        
    def get_node_type(self):
        return self._node_type
