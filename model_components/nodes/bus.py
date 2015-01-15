from logging import debug, info, warning
from itertools import count

from numpy import append, nan

from .node import Node
from model_components import impedance_admittance_wrangler
# from power_network_helper_functions import jacobian_hij_helper, jacobian_nij_helper, jacobian_kij_helper, jacobian_lij_helper

from IPython import embed


class Bus(Node):
    _bus_ids = count(0)
    
    def __init__(self, dgr=None, loads=None, V0=None, theta0=None, shunt_z=(), shunt_y=()):
        if type(dgr) is list:
            raise TypeError('Only a single generator can be attached to ')
        
        # try to inherit the initial voltage of an attached generator or load
        if (V0 is None or theta0 is None) and (dgr is not None or loads is not None):
            # prefer to inherit the initial voltage of a dgr over a load
            if dgr is not None:
                inherited_V0, inherited_theta0 = dgr.get_initial_voltage()
            elif loads is not None:
                # if there are multiple loads attached, inherit the initial voltage of the first in the list
                if type(loads) is not list:
                    inherited_V0, inherited_theta0 = loads.get_initial_voltage()
                else:
                    inherited_V0, inherited_theta0 = loads[0].get_initial_voltage()
                
            # only inherit the part of the initial voltage that was omitted
            if V0 is None:
                V0 = inherited_V0
            if theta0 is None:
                theta0 = inherited_theta0
                
        Node.__init__(self, V0, theta0)
        
        self._bus_id = self._bus_ids.next() + 1
        
        self._node_type = 'bus'
        
        if dgr is not None:
            # print dgr.__class__.__bases__
            dgr_V0, dgr_theta0 = dgr.get_initial_voltage()
            if dgr_V0 != V0:
                info('The initial voltage magnitude of the attached DGR will be overwritten by the value of the bus')
                self.copy_bus_voltage_magnitude_to_generator()
            if dgr_theta0 != theta0:
                info('The initial voltage angle of the attached DGR will be overwritten by the value of the bus')
                self.copy_bus_voltage_angle_to_generator()
            self.dgr = dgr
                
        
        if loads is not None:
            # make loads a single element list if only a single one provided to allow th same code
            if type(loads) is not list:
                loads = [loads]
            for load in loads:
                self.add_load(load)
                
        self.shunt_y = impedance_admittance_wrangler(shunt_z, shunt_y)


            
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])


    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<Bus, Node #%i>' % (self.get_id())]
        
        current_states = []
        V, theta = self.get_current_voltage()
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
        
        try:
            if self.loads != []:    
                object_info.append('%sConnected loads:' % (''.rjust(indent_level_increment)))
            else:
                object_info.append('%sNo loads connected!' % (''.rjust(indent_level_increment)))
        
            for node in self.loads:
                object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), line)
                                    for line in node.repr_helper(simple=True, indent_level_increment=indent_level_increment)])
        except AttributeError:
            pass
        
        return object_info


    def get_bus_id(self):
        return self._bus_id
        
        
    def get_load_by_node_id(self, node_id):
        for load in self.get_connected_loads():
            if load.get_id() == node_id:
                return load
        
        return None


    def add_load(self, load):
        loads = self.get_connected_loads()
            
        load_V0, load_theta0 = load.get_initial_voltage()
        bus_V0, bus_theta0 = self.get_initial_voltage()

        if len(load.V) != 1:
            info('Resetting load voltage magnitude array.')
        if load_V0 != bus_V0:
            info('Overwriting initial voltage magnitude of load (node %i) to match bus.' % (load.get_id()))
    
        if len(load.theta) != 1:
            info('Resetting load voltage angle array.')
        if load_theta0 != bus_theta0:
            info('Overwriting initial voltage angle of load (node %i) to match bus.' % (load.get_id()))
            
        self.copy_bus_voltage_to_child(load)
        
        if loads == []:
            self.loads = [load]
        else:
            self.loads.append(load)
        
    
    def get_connected_loads(self):
        try:
            loads = self.loads
        except AttributeError:
            loads = []
        
        return loads


    def update_voltage(self, V, theta, replace=False, copy_to_child_nodes=True):
        Vout = self.update_voltage_magnitude(V, replace=replace, copy_to_child_nodes=copy_to_child_nodes)
        thetaOut = self.update_voltage_angle(theta, replace=replace, copy_to_child_nodes=copy_to_child_nodes)
        return Vout, thetaOut            
            
    
    def update_voltage_magnitude(self, V, replace=False, copy_to_child_nodes=True):
        if replace is True:
            return self.replace_voltage_magnitude(V, copy_to_child_nodes=copy_to_child_nodes)
        else:
            return self.append_voltage_magnitude(V, copy_to_child_nodes=copy_to_child_nodes)
            
    
    def update_voltage_angle(self, theta, replace=False, copy_to_child_nodes=True):
        if replace is True:
            return self.replace_voltage_angle(theta, copy_to_child_nodes=copy_to_child_nodes)
        else:
            return self.append_voltage_angle(theta, copy_to_child_nodes=copy_to_child_nodes)


    def replace_voltage(self, V, theta, copy_to_child_nodes=True):
        Vout = self.replace_voltage_magnitude(V, copy_to_child_nodes=False)
        thetaOut = self.replace_voltage_angle(theta, copy_to_child_nodes=False)
        # save to child nodes here rather than do it twice above
        if copy_to_child_nodes is True:
            self.copy_bus_voltage_to_generator_and_loads()
        return Vout, thetaOut


    def replace_voltage_magnitude(self, V, copy_to_child_nodes=True):
        Vout = Node.replace_voltage_magnitude(self, V)
        if copy_to_child_nodes is True:
            self.copy_bus_voltage_to_generator_and_loads()
        return Vout
        
    
    def replace_voltage_angle(self, theta, copy_to_child_nodes=True):
        thetaOut = Node.replace_voltage_angle(self, theta)
        if copy_to_child_nodes is True:
            self.copy_bus_voltage_to_generator_and_loads()
        return thetaOut
        
    
    def append_voltage(self, V, theta, copy_to_child_nodes=True):
        Vout = self.append_voltage_magnitude(V, copy_to_child_nodes=False)
        thetaOut = self.append_voltage_angle(theta, copy_to_child_nodes=False)
        if copy_to_child_nodes is True:
            self.copy_bus_voltage_to_generator_and_loads()
        return Vout, thetaOut
        
        
    def append_voltage_magnitude(self, V, copy_to_child_nodes=True):
        Vout = Node.append_voltage_magnitude(self, V)
        if copy_to_child_nodes is True:
            self.copy_bus_voltage_to_generator_and_loads()
        return Vout
        
    
    def append_voltage_angle(self, theta, copy_to_child_nodes=True):
        thetaOut = Node.append_voltage_angle(self, theta)
        if copy_to_child_nodes is True:
            self.copy_bus_voltage_to_generator_and_loads()
        return thetaOut
        
    
    def reset_voltage_to_unity_magnitude_zero_angle(self):
        self.set_initial_voltage(1.0, 0.0)
        self.copy_bus_voltage_to_generator_and_loads()
        
    
    def reset_voltage_to_zero_angle(self):
        self.set_initial_voltage(self.V[-1], 0.0)
        self.copy_bus_voltage_to_generator_and_loads()


    def copy_bus_voltage_to_generator_and_loads(self):
        self.copy_bus_voltage_to_generator()
        self.copy_bus_voltage_to_loads()
            

    def copy_bus_voltage_magnitude_to_generator_and_loads(self):
        self.copy_bus_voltage_magnitude_to_generator()
        self.copy_bus_voltage_magnitude_to_loads()
            
            
    def copy_bus_voltage_angle_to_generator_and_loads(self):
        self.copy_bus_voltage_angle_to_generator()
        self.copy_bus_voltage_angle_to_loads()
            

    def copy_bus_voltage_to_generator(self):
        self.copy_bus_voltage_magnitude_to_generator()
        self.copy_bus_voltage_angle_to_generator()
            

    def copy_bus_voltage_magnitude_to_generator(self):
        try:
            self.copy_bus_voltage_magnitude_to_child(self.dgr)
        except AttributeError:
            debug('No generator attached to which to copy voltage magnitude!')
            
            
    def copy_bus_voltage_angle_to_generator(self):
        try:
            self.copy_bus_voltage_angle_to_child(self.dgr)
        except AttributeError:
            debug('No generator attached to which to copy voltage angle!')


    def copy_bus_voltage_to_loads(self):
        try:            
            for load in self.loads:
                self.copy_bus_voltage_to_child(load)
        except AttributeError:
            debug('No loads attached to which to copy voltage!')
            

    def copy_bus_voltage_magnitude_to_loads(self):
        try:
            for load in self.loads:
                self.copy_bus_voltage_magnitude_to_child(load)
        except AttributeError:
            debug('No loads attached to which to copy voltage magnitude!')
            
            
    def copy_bus_voltage_angle_to_loads(self):
        try:
            for load in self.loads:
                self.copy_bus_voltage_angle_to_child(load)
        except AttributeError:
            debug('No loads attached to which to copy voltage angle!')


    def copy_bus_voltage_to_child(self, child):
        self.copy_bus_voltage_magnitude_to_child(child)
        self.copy_bus_voltage_angle_to_child(child)
            
    
    def copy_bus_voltage_magnitude_to_child(self, child):
        child.V = self.V
    
    
    def copy_bus_voltage_angle_to_child(self, child):
        child.theta = self.theta
        

    def is_pv_bus(self):
        """
            simply a wrapper around voltage the is_static method for voltage magnitude
        """
        return self.is_voltage_magnitude_static()
        # if self.get_node_type() == 'pv_bus':
        #     return True
        # elif self.is_temporary_pv_bus() is True:
        #     return True
        #
        # return False


    def has_dynamic_dgr_attached(self):
        try:
            model = self.dgr.check_for_generator_model()
            return True
        except AttributeError:
            return False


    def make_temporary_pv_bus(self):
        return self.make_voltage_magnitude_static()


    def stop_temporary_pv_bus(self):
        return self.stop_voltage_magnitude_static()


    def is_temporary_pv_bus(self):
        if self.has_dynamic_dgr_attached() is True and self.is_pv_bus() is True:
            return True
        return False


    def get_specified_real_reactive_power(self):
        P = 0
        Q = 0
        if self._node_type == 'pv_bus':
            PVp, _ = self.get_current_real_reactive_power()
            P += PVp
        elif self.has_dynamic_dgr_attached() is True:
            if self.is_temporary_pv_bus() is True:
                setpoints = self.dgr.get_current_setpoints(as_dictionary=True)
                governor_setpoint = setpoints['u']
                P += governor_setpoint
            else:
                Pgen, Qgen = self.dgr.get_real_reactive_power_output()
                if Pgen != nan:
                    P += Pgen
                if Qgen != nan:
                    Q += Qgen
        try:
            for load in self.loads:
                if load._node_type == 'constant_power_load':
                    P -= load.P
                    Q -= load.Q
        except AttributeError:
            pass
                    
                
        return P, Q


    def is_voltage_magnitude_static(self):
        """
        Indicates whether or not the voltage magnitude for this bus should remain constant for static simulations, i.e.,
        power flow computations.  The voltage_magnitude_is_static property should be set by the subclass derived from
        the Bus superclass; if this property is not set, it defaults to False.

        Args:
            self: the instance of the bus object

        Returns:
            A boolean value indicating whether or not the voltage magnitude for this bus should remain constant for static
            simulations. The default is False.
            
            True: if the voltage magnitude should remain constant.
            False: otherwise

        """
        try:
            return self.voltage_magnitude_static
        except AttributeError:
            return False


    def is_voltage_angle_static(self):
        """
        Indicates whether or not the voltage angle for this bus should remain constant for static simulations, i.e.,
        power flow computations.  The voltage_angle_is_static property should be set by the subclass derived from
        the Bus superclass; if this property is not set, it defaults to False.

        Args:
            self: the instance of the bus object

        Returns:
            A boolean value indicating whether or not the voltage angle for this bus should remain constant for static
            simulations. The default is False.
            
            True: if the voltage angle should remain constant.
            False: otherwise

        """
        try:
            return self.voltage_angle_static
        except AttributeError:
            return False
            
    
    def is_voltage_static(self):
        return self.is_voltage_magnitude_static(), self.is_voltage_angle_static()


    def make_voltage_magnitude_static(self):
        self.voltage_magnitude_static = True
        return self.is_voltage_magnitude_static()


    def make_voltage_angle_static(self):
        self.voltage_angle_static = True
        return self.is_voltage_angle_static()


    def make_voltage_static(self):
        _ = self.make_voltage_magnitude_static()
        _ = self.make_voltage_angle_static()
        return self.is_voltage_static()


    def stop_voltage_magnitude_static(self):
        self.voltage_magnitude_static = False
        return self.is_voltage_magnitude_static()


    def stop_voltage_angle_static(self):
        self.voltage_angle_static = False
        return self.is_voltage_angle_static()


    def stop_voltage_static(self):
        _ = self.stop_voltage_magnitude_static()
        _ = self.stop_voltage_angle_static()
        return self.is_voltage_static()


    def get_jacobian_block(self, Yij, Vpolar_i=None, Vpolar_i_static=None, Vpolar_j=None, Vpolar_j_static=None):
        pass
        # # admittance is stored as a tuple: conductance, susceptance
        # Gij, Bij = Yij
        # # bus i (and its associated properties) is this bus, bus j is connected bus for which this block is being computed
        # # The properties for bus i are optional to allow for parallelization of Jacobian computation
        # if Vpolar_i is None:
        #     Vpolar_i = self.get_current_voltage()
        #
        # if Vpolar_i_static is None:
        #     Vpolar_i_static = self.voltage_is_static()
        # # stored as a tuple where the elements indicate if the magnitude and angle are static, respectively
        # Vi_static, thetai_static = Vpolar_i_static
        #
        # # if either of the properties for bus j are omitted, it's assumed that j = i, i.e., the self block is being computed
        # if Vpolar_j is None or Vpolar_j_static is None:
        #     self_block = True
        #     Vpolar_j = Vpolar_i
        #     Vj_static = Vi_static
        #     thetaj_static = thetai_static
        # else:
        #     self_block = False
        #
        # # this block can be of size 1x1, 2x1, 1x2, or 2x2; default to 1x1
        # num_rows = 1
        # num_cols = 1
        #
        # if self_block is False:
        #     H = jacobian_hij_helper(Vpolar_i, Vpolar_j, Gij, Bij)
                    
