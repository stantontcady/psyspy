from itertools import count

from numpy import append

from helper_functions import set_initial_conditions


class Bus(object):
    _bus_ids = count(0)
    
    def __init__(self, nodes=None, V0=None, theta0=None):
        self._bus_id = self._bus_ids.next() + 1
        
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
        
        self.nodes = []
        
        if nodes is not None:
            if type(nodes) is not list:
                nodes = [nodes]
            for node in nodes:
                self.add_node(node)
            
    def __repr__(self, simple=False, base_indent=0):
        indent_level_increment = 2
        
        object_info = []
        current_states = []
        
        current_states.append('Voltage magnitude, V: %0.3f pu' % (self.V[-1]))
        current_states.append('Voltage angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), self.theta[-1]))
        
        object_info.append('<Bus #%i>' % (self._bus_id))
        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        
        if self.nodes != []:    
            object_info.append('%sConnected nodes:' % (''.rjust(indent_level_increment)))
        else:
            object_info.append('%sNo nodes connected!' % (''.rjust(indent_level_increment)))

        object_info = '\n'.join(['%s%s' % ((''.rjust(base_indent), line)) for line in object_info])
        
        for node in self.nodes:
            object_info += '\n%s' % (node.__repr__(simple=True, base_indent=(base_indent + 2*indent_level_increment)))
        
        return object_info
        
    def get_id(self):
        return self._bus_id
        
    def set_initial_conditions(self, V0=None, theta0=None):
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
    
    def add_node(self, node):
        if len(node.V) != 1:
            print 'Resetting node voltage magnitude array.'
        if node.V[0] != self.V[0]:
            print 'Overwriting initial voltage magnitude of node %i to match bus.' % (node.get_id())
            set_initial_conditions(node, 'V', self.V[0])
    
        if len(node.theta) != 1:
            print 'Resetting node voltage angle array.'
        if node.theta[0] != self.theta[0]:
            print 'Overwriting initial voltage angle of node %i to match bus.' % (node.get_id())
            set_initial_conditions(node, 'theta', self.theta[0])
    
        self.nodes.append(node)
    
    def update_states(self, V, theta):
        self.V = append(self.V, V)
        self.theta = append(self.theta, theta)
        for node in self.nodes:
            node.update_states(V, theta)
        