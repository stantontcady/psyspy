from itertools import count

from helper_functions import set_initial_conditions


class Bus(object):
    _bus_ids = count(0)
    
    def __init__(self, nodes=None, V0=None, theta0=None):
        self.bus_id = self._bus_ids.next() + 1
        
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
        
        self.nodes = []
        
        for node in nodes:
            if len(node.V) != 1:
                print 'Resetting node voltage magnitude array.'
            if V0 is not None and node.V[0] != V0:
                print 'Overwriting initial node voltage magnitude to match bus.'
            set_initial_conditions(node, 'V', V0)
            
            if len(node.theta) != 1:
                print 'Resetting node voltage angle array.'
            if theta0 is not None and node.theta[0] != theta0:
                print 'Overwriting initial node voltage angle to match bus.'
            set_initial_conditions(node, 'theta', theta0)
            
            self.nodes.append(node)
            
    def __repr__(self):
        object_description = '<Bus #%i>' % (self.bus_id)
        V = '    Voltage magnitude, V: %0.3f pu' % self.V[-1]
        theta = '    Voltage angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), self.theta[-1])
        current_states = '  Current state values:\n%s\n%s' % (V, theta)
        
        connected_nodes = '  Connected nodes'
        for node in self.nodes:
            connected_nodes += '\n%s' % (node.__repr__(simple=True, base_indent=4))
        
        return '%s\n%s\n%s' % (object_description, current_states, connected_nodes)