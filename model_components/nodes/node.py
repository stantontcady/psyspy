from itertools import count

from numpy import array, append, nan

from model_components import set_initial_conditions


class Node(object):
    _node_ids = count(0)
    
    def __init__(self, V0=None, theta0=None):
        self._node_id = self._node_ids.next() + 1
        
        if V0 is None:
            V0 = 1
        if theta0 is None:
            theta0 = 0

        _, _ = self.set_initial_voltage(V0, theta0)
        
        self._node_type = 'Node'
        
        
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])

        
    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<Node #%i>' % (self._node_id)]
        
        current_states = []
        V, theta = self.get_node_voltage()
        current_states.append('Magnitude, V: %0.3f pu' % (V))
        current_states.append('Angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), theta))
        
        if current_states != []:
            object_info.append('%sCurrent voltage:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
            
        return object_info

        
    def update_voltage(self, V, theta, replace=False):
        Vout = self.update_voltage_magnitude(V, replace=replace)
        thetaOut = self.update_voltage_angle(theta, replace=replace)
        return Vout, thetaOut            
            
    
    def update_voltage_magnitude(self, V, replace=False):
        if replace is True:
            return self.replace_voltage_magnitude(V)
        else:
            return self.append_voltage_magnitude(V)
            
    
    def update_voltage_angle(self, theta, replace=False):
        if replace is True:
            return self.replace_voltage_angle(theta)
        else:
            return self.append_voltage_angle(theta)


    def replace_voltage(self, V, theta):
        Vout = self.replace_voltage_magnitude(V)
        thetaOut = self.replace_voltage_angle(theta)
        return Vout, thetaOut


    def replace_voltage_magnitude(self, V):
        self.V[-1] = V
        return self.get_current_voltage_magnitude()
        
    
    def replace_voltage_angle(self, theta):
        self.theta[-1] = theta
        return self.get_current_voltage_angle()
        
    
    def append_voltage(self, V, theta):
        Vout = self.append_voltage_magnitude(V)
        thetaOut = self.append_voltage_angle(theta)
        return Vout, thetaOut
        
        
    def append_voltage_magnitude(self, V):
        self.V = append(self.V, V)
        return self.get_current_voltage_magnitude()
        
    
    def append_voltage_angle(self, theta):
        self.theta = append(self.theta, theta)
        return self.get_current_voltage_angle()
        
    
    def reset_voltage_to_unity_magnitude_zero_angle(self):
        return self.set_initial_node_voltage(1.0, 0.0)
        
    
    def reset_voltage_to_zero_angle(self):
        return self.set_initial_node_voltage(self.V[-1], 0.0)

        
    def set_initial_voltage(self, V0=None, theta0=None):
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
        return self.get_current_voltage()
        
    
    def get_initial_voltage(self):
        return self.get_initial_voltage_magnitude(), self.get_initial_voltage_angle()
        

    def get_initial_voltage_magnitude(self):
        return self.get_voltage_magnitude_by_index(0)
        

    def get_initial_voltage_angle(self):
        return self.get_voltage_angle_by_index(0)
    
        
    def get_current_voltage(self):
        return self.get_current_voltage_magnitude(), self.get_current_voltage_angle()
       
        
    def get_current_voltage_magnitude(self):
        return self.get_voltage_magnitude_by_index(-1)
        

    def get_current_voltage_angle(self):
        return self.get_voltage_angle_by_index(-1)
        
    
    def get_voltage_by_index(self, index):
        return self.get_voltage_magnitude_by_index(index), self.get_voltage_angle_by_index(index)
        
        
    def get_voltage_magnitude_by_index(self, index):
        try:
            return self.V[index]
        except IndexError:
            return nan
            
    
    def get_voltage_angle_by_index(self, index):
        try:
            return self.theta[index]
        except IndexError:
            return nan
        
    
    def _voltage_helper(self, V=None, theta=None):
        if V is None:
            V = self.get_current_voltage_magnitude()
        if theta is None:
            theta = self.get_current_voltage_angle()
        return V, theta


    def get_id(self):
        return self._node_id

        
    def get_node_type(self):
        return self._node_type
