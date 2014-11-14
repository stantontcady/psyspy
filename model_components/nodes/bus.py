from itertools import count

from numpy import append

from .node import Node
from model_components import impedance_admittance_wrangler


class Bus(Node):
    _bus_ids = count(0)
    
    def __init__(self, nodes=None, V0=None, theta0=None, shunt_z=(), shunt_y=()):
        
        if (V0 is None or theta0 is None) and nodes is not None:
            if type(nodes) is not list:
                node_V0, node_theta0 = nodes.get_current_node_voltage()
            else:
                node_V0, node_theta0 = nodes[0].get_current_node_voltage()
            if V0 is None:
                V0 = node_V0
            if theta0 is None:
                theta0 = node_theta0

        
        Node.__init__(self, V0, theta0)
        
        self._bus_id = self._bus_ids.next() + 1
        
        self._node_type = 'bus'
        
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
    
    def update_voltage(self, V, theta, replace=False, save_to_child_nodes=True):
        Vout = self.update_voltage_magnitude(V, replace=replace, save_to_child_nodes=save_to_child_nodes)
        thetaOut = self.update_voltage_angle(theta, replace=replace, save_to_child_nodes=save_to_child_nodes)
        return Vout, thetaOut            
            
    
    def update_voltage_magnitude(self, V, replace=False, save_to_child_nodes=True):
        if replace is True:
            return self.replace_voltage_magnitude(V, save_to_child_nodes=save_to_child_nodes)
        else:
            return self.append_voltage_magnitude(V, save_to_child_nodes=save_to_child_nodes)
            
    
    def update_voltage_angle(self, theta, replace=False, save_to_child_nodes=True):
        if replace is True:
            return self.replace_voltage_angle(theta, save_to_child_nodes=save_to_child_nodes)
        else:
            return self.append_voltage_angle(theta, save_to_child_nodes=save_to_child_nodes)


    def replace_voltage(self, V, theta, save_to_child_nodes=True):
        Vout = self.replace_voltage_magnitude(V, save_to_child_nodes=False)
        thetaOut = self.replace_voltage_angle(theta, save_to_child_nodes=False)
        if save_to_child_nodes is True:
            self.save_bus_voltage_to_child_nodes()
        return Vout, thetaOut


    def replace_voltage_magnitude(self, V, save_to_child_nodes=True):
        Vout = self.replace_node_voltage_magnitude(V)
        if save_to_child_nodes is True:
            self.save_bus_voltage_to_child_nodes()
        return Vout
        
    
    def replace_voltage_angle(self, theta, save_to_child_nodes=True):
        thetaOut = self.replace_node_voltage_angle(theta)
        if save_to_child_nodes is True:
            self.save_bus_voltage_to_child_nodes()
        return thetaOut
        
    
    def append_voltage(self, V, theta, save_to_child_nodes=True):
        Vout = self.append_voltage_magnitude(V, save_to_child_nodes=False)
        thetaOut = self.append_voltage_angle(theta, save_to_child_nodes=False)
        if save_to_child_nodes is True:
            self.save_bus_voltage_to_child_nodes()
        return Vout, thetaOut
        
        
    def append_voltage_magnitude(self, V, save_to_child_nodes=True):
        Vout = self.append_node_voltage_magnitude(V)
        if save_to_child_nodes is True:
            self.save_bus_voltage_to_child_nodes()
        return Vout
        
    
    def append_voltage_angle(self, theta, save_to_child_nodes=True):
        thetaOut = self.append_node_voltage_angle(theta)
        if save_to_child_nodes is True:
            self.save_bus_voltage_to_child_nodes()
        return thetaOut
        
    
    def reset_voltage_to_unity_magnitude_zero_angle(self):
        self.set_initial_node_voltage(1.0, 0.0)
        self.save_bus_voltage_to_child_nodes()
        
    
    def reset_voltage_to_zero_angle(self):
        self.set_initial_node_voltage(self.V[-1], 0.0)
        self.save_bus_voltage_to_child_nodes()
            
            
    def save_bus_voltage_to_child_nodes(self):
        for node in self.child_nodes:
            node.V = self.V
            node.theta = self.theta
        

    def is_pv_bus(self):
        if self.get_node_type() == 'pv_bus':
            return True
        # for node in self.child_nodes:
        #     node_type = node.get_node_type()
        #     if node_type == 'DGR' or node_type == 'SynchronousDGR':
        #         return True
        return False

        
    def has_dynamic_generator(self):
        for node in self.child_nodes:
            node_type = node.get_node_type()
            print node_type
            if node_type == 'synchronous_dgr':
                return True
                
        return False

        
    def get_specified_real_reactive_power(self):
        P = 0
        Q = 0
        if self._node_type == 'pv_bus':
            PVp, _ = self.get_current_real_reactive_power()
            P += PVp
        for node in self.child_nodes:
            if node._node_type == 'constant_power_load':
                P -= node.P
                Q -= node.Q
                
        return P, Q
