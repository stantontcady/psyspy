from itertools import count

from numpy import append

from .node import Node
from model_components import impedance_admittance_wrangler


class Bus(Node):
    _bus_ids = count(0)
    
    def __init__(self, nodes=None, V0=None, theta0=None, shunt_z=(), shunt_y=()):
        
        Node.__init__(self, V0, theta0)
        
        self._bus_id = self._bus_ids.next() + 1
        
        self._bus_type = 'Bus'
        
        self.child_nodes = []
        
        if nodes is not None:
            if type(nodes) is not list:
                nodes = [nodes]
            for node in nodes:
                self.add_child_node(node)
                
        self.shunt_y = impedance_admittance_wrangler(shunt_z, shunt_y)

            
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])


    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<Bus, Node #%i>' % (self.get_id())]
        
        current_states = []
        V, theta = self.get_current_node_voltage()
        current_states.append('Magnitude, V: %0.3f pu' % (V))
        current_states.append('Angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), theta))
        
        if current_states != []:
            object_info.append('%sCurrent voltage:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        
        if self.shunt_y != (0, 0):
            object_info.append('%sShunt admittance:' % (''.rjust(indent_level_increment)))
            if self.shunt_y[0] != 0:
                object_info.append('%sConductance: %0.3f' % (''.rjust(2*indent_level_increment), self.shunt_y[0]))
            if self.shunt_y[1] != 0:
                object_info.append('%sSusceptance: %0.3f' % (''.rjust(2*indent_level_increment), self.shunt_y[1]))
        
        if self.child_nodes != []:    
            object_info.append('%sConnected nodes:' % (''.rjust(indent_level_increment)))
        else:
            object_info.append('%sNo nodes connected!' % (''.rjust(indent_level_increment)))
        
        for node in self.child_nodes:
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), line)
                                for line in node.repr_helper(simple=True, indent_level_increment=indent_level_increment)])
        
        return object_info
        

    def get_type(self):
        return self._bus_type


    def get_bus_id(self):
        return self._bus_id


    def add_child_node(self, node):
        if len(node.V) != 1:
            print 'Resetting node voltage magnitude array.'
        if node.V[0] != self.V[0]:
            print 'Overwriting initial voltage magnitude of node %i to match bus.' % (node.get_id())
    
        if len(node.theta) != 1:
            print 'Resetting node voltage angle array.'
        if node.theta[0] != self.theta[0]:
            print 'Overwriting initial voltage angle of node %i to match bus.' % (node.get_id())
            
        node.set_initial_node_voltage(self.V[0], self.theta[0])
    
        self.child_nodes.append(node)

    
    def update_voltage(self, V, theta):
        self.update_node_voltage(V, theta)
        for node in self.child_nodes:
            node.V = self.V
            node.theta = self.theta
            # node.update_node_voltage(V, theta)
        

    def has_generator_attached(self):
        if self.get_node_type() == 'PVBus':
            return True
        for node in self.child_nodes:
            node_type = node.get_node_type()
            if node_type == 'DGR' or node_type == 'SynchronousDGR':
                return True
        return False
        
    def get_specified_real_reactive_power(self):
        P = 0
        Q = 0
        if self._node_type == 'PVBus':
            PVp, PVq = self.get_current_real_reactive_power()
            P += PVp
            Q += PVq
        for node in self.child_nodes:
            if node._node_type == 'ConstantPowerLoad':
                P -= node.P
                Q -= node.Q
                
        return P, Q

        