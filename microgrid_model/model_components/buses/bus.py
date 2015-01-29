from logging import debug, info, warning
from itertools import count

from numpy import append, nan

from microgrid_model.exceptions import BusError, ModelError
from ..helper_functions import impedance_admittance_wrangler, set_initial_conditions
from ..models import Model

class Bus(object):
    _bus_ids = count(0)
    
    def __init__(self, model=None, V0=None, theta0=None, shunt_z=(), shunt_y=()):
        if model is None:
            model = Model()
        elif isinstance(model, Model) is False:
            raise ModelError('provided model must an instance of the Model type or a subclass thereof')
            
        self.model = model

        if V0 is None:
            V0 = 1
        if theta0 is None:
            theta0 = 0

        _, _ = self.set_initial_voltage_polar((V0, theta0))

        self._bus_id = self._bus_ids.next() + 1
                
        self.shunt_y = impedance_admittance_wrangler(shunt_z, shunt_y)


    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])


    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<Bus #%i>' % (self.get_id())]
        
        current_states = []
        V, theta = self.get_current_voltage_polar()
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
        
        # try:
        #     if self.loads != []:
        #         object_info.append('%sConnected loads:' % (''.rjust(indent_level_increment)))
        #     else:
        #         object_info.append('%sNo loads connected!' % (''.rjust(indent_level_increment)))
        #
        #     for node in self.loads:
        #         object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), line)
        #                             for line in node.repr_helper(simple=True, indent_level_increment=indent_level_increment)])
        # except AttributeError:
        #     pass
        
        return object_info

        
    def get_id(self):
        return self._bus_id
        
        
    def prepare_for_dynamic_simulation_initial_value_calculation(self):
        return self.model.prepare_for_dynamic_simulation_initial_value_calculation()


    def prepare_for_dynamic_simulation(self):
        # 
        return self.model.prepare_for_dynamic_simulation()


    def initialize_dynamic_states(self, Snetwork):
        Vpolar = self.get_current_voltage_polar()
        return self.model.initialize_dynamic_states(Vpolar, Snetwork)
        
    
    def get_current_dynamic_state_array(self):
        return self.model.get_current_dynamic_state_array()


    def get_dynamic_state_time_derivative_array(self):
        Vpolar = self.get_current_voltage_polar()
        return self.model.get_dynamic_state_time_derivative_array(Vpolar)


    def update_dynamic_states(self, new_state_array):
        return self.model.update_dynamic_states(new_state_array)


    def get_apparent_power_derivatives(self, Vpolar=None):
        if Vpolar is None:
            Vpolar = self.get_current_voltage_polar()
        return self.model.get_apparent_power_derivatives(Vpolar)


    def get_current_dynamic_angular_velocity(self):
        return self.model.get_current_dynamic_angular_velocity()


    def set_reference_dynamic_angular_velocity(self, reference_velocity):
        if reference_velocity is None:
            pass
        else:
            return self.model.set_reference_dynamic_angular_velocity(reference_velocity)


    def save_bus_voltage_polar_to_model(self):
        Vpolar = self.get_current_voltage_polar()
        return self.model.save_bus_voltage_polar(Vpolar)


    def update_dynamic_states(self, numerical_integration_method):
        return self.model.update_dynamic_states(numerical_integration_method)


    def set_initial_voltage_polar(self, Vpolar=()):
        if Vpolar == ():
            V0 = None
            theta0 = None
        else:
            try:
                V0 = Vpolar[0]
                theta0 = Vpolar[1]
            except IndexError:
                V0 = None
                theta0 = None
        set_initial_conditions(self, 'V', V0)
        set_initial_conditions(self, 'theta', theta0)
        return self.get_initial_voltage_polar()


    def get_initial_voltage_polar(self):
        return self.get_initial_voltage_magnitude(), self.get_initial_voltage_angle()
        

    def get_initial_voltage_magnitude(self):
        return self.get_voltage_magnitude_by_index(0)
        

    def get_initial_voltage_angle(self):
        return self.get_voltage_angle_by_index(0)
    
        
    def get_current_voltage_polar(self):
        return self.get_current_voltage_magnitude(), self.get_current_voltage_angle()
       
        
    def get_current_voltage_magnitude(self):
        return self.get_voltage_magnitude_by_index(-1)
        

    def get_current_voltage_angle(self):
        return self.get_voltage_angle_by_index(-1)
        
        
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


    def update_voltage_polar(self, Vpolar, replace=False):
        try:
            V = Vpolar[0]
            theta = Vpolar[1]
        except IndexError:
            raise BusError('polar voltage does not have two components')
        
        Vout = self.update_voltage_magnitude(V, replace=replace)
        thetaOut = self.update_voltage_angle(theta, replace=replace)
        return Vout, thetaOut            
            
    
    def update_voltage_magnitude(self, V, replace=False):
        if replace is True:
            return self._replace_voltage_magnitude(V)
        else:
            return self._append_voltage_magnitude(V)
            
    
    def update_voltage_angle(self, theta, replace=False):
        if replace is True:
            return self._replace_voltage_angle(theta)
        else:
            return self._append_voltage_angle(theta)


    def _replace_voltage_magnitude(self, V):
        self.V[-1] = V
        return self.get_current_voltage_magnitude()
        
    
    def _replace_voltage_angle(self, theta):
        self.theta[-1] = theta
        return self.get_current_voltage_angle()
        
        
    def _append_voltage_magnitude(self, V):
        self.V = append(self.V, V)
        return self.get_current_voltage_magnitude()
        
    
    def _append_voltage_angle(self, theta):
        self.theta = append(self.theta, theta)
        return self.get_current_voltage_angle()
        
    
    def reset_voltage_to_unity_magnitude_zero_angle(self):
        self.set_initial_voltage_polar((1.0, 0.0))
        
    
    def reset_voltage_to_zero_angle(self):
        self.set_initial_voltage_polar((self.V[-1], 0.0))


    def _voltage_helper(self, V=None, theta=None):
        return self._polar_voltage_helper((V, theta))


    def _polar_voltage_helper(self, Vpolar=None):
        if Vpolar is None:
            V, theta = self.get_current_voltage() 
        else:
            try:
                if Vpolar[0] is None:
                    V = self.get_current_voltage_magnitude()
                if Vpolar[1] is None:
                    theta = self.get_current_voltage_angle()
            except IndexError:
                raise BusError('polar voltage does not have two components')
        
        return V, theta


    def is_pv_bus(self):
        """
            simply a wrapper around voltage the is_static method for voltage magnitude
        """
        return self.is_voltage_magnitude_static()


    def shift_voltage_angles(self, angle_to_shift):
        current_angle = self.get_current_voltage_angle()
        self.update_voltage_angle((current_angle-angle_to_shift), replace=True)
        if self.has_dynamic_model() is True:
            _ = self.model.shift_dynamic_internal_voltage_angle(angle_to_shift)

            
    def make_slack_bus(self):
        v_static, theta_static = self.model.make_voltage_polar_static()
        if v_static is not True and theta_static is not True:
            raise ModelError('cannot change static flags for model')


    def unmake_slack_bus(self):
        v_static, theta_static = self.model.unmake_voltage_polar_static()
        if v_static is not False and theta_static is not False:
            raise ModelError('cannot change static flags for model')


    def has_dynamic_model(self):
        return self.model.is_dynamic
        
    
    def has_generator_model(self):
        return self.model.is_generator


    def get_apparent_power_injection(self):
        Vpolar = self.get_current_voltage_polar()
        return self.model.get_apparent_power_injection(Vpolar)
        # P = 0
        # Q = 0
        # if self._node_type == 'pv_bus':
        #     PVp, _ = self.get_current_real_reactive_power()
        #     P += PVp
        # elif self.has_dynamic_dgr_attached() is True:
        #     if self.is_temporary_pv_bus() is True:
        #         setpoints = self.dgr.get_current_setpoints(as_dictionary=True)
        #         governor_setpoint = setpoints['u']
        #         P += governor_setpoint
        #     else:
        #         Pgen, Qgen = self.dgr.get_real_reactive_power_output()
        #         if Pgen != nan:
        #             P += Pgen
        #         if Qgen != nan:
        #             Q += Qgen
        # try:
        #     for load in self.loads:
        #         if load._node_type == 'constant_power_load':
        #             P -= load.P
        #             Q -= load.Q
        # except AttributeError:
        #     pass
        #
        #
        # return P, Q
        
    def is_voltage_polar_static(self):
        return self.is_voltage_magnitude_static(), self.is_voltage_angle_static()


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
            return self.model.is_voltage_magnitude_static()
        except AttributeError, ModelError:
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
            return self.model.is_voltage_angle_static()
        except AttributeError, ModelError:
            return False
            
    


    # def make_voltage_magnitude_static(self):
    #     self.voltage_magnitude_static = True
    #     return self.is_voltage_magnitude_static()
    #
    #
    # def make_voltage_angle_static(self):
    #     self.voltage_angle_static = True
    #     return self.is_voltage_angle_static()
    #
    #
    # def make_voltage_static(self):
    #     _ = self.make_voltage_magnitude_static()
    #     _ = self.make_voltage_angle_static()
    #     return self.is_voltage_static()
    #
    #
    # def stop_voltage_magnitude_static(self):
    #     self.voltage_magnitude_static = False
    #     return self.is_voltage_magnitude_static()
    #
    #
    # def stop_voltage_angle_static(self):
    #     self.voltage_angle_static = False
    #     return self.is_voltage_angle_static()
    #
    #
    # def stop_voltage_static(self):
    #     _ = self.stop_voltage_magnitude_static()
    #     _ = self.stop_voltage_angle_static()
    #     return self.is_voltage_static()


    # def get_jacobian_block(self, Yij, Vpolar_i=None, Vpolar_i_static=None, Vpolar_j=None, Vpolar_j_static=None):
    #     pass
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
                    