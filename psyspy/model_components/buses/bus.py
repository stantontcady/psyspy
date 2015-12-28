from logging import debug, info, warning
from itertools import count
from math import pi

from numpy import append, nan

from ...exceptions import BusError, ModelError
from ...helper_functions import impedance_admittance_wrangler, set_initial_conditions
from ..models import Model


class Bus(object):
    _bus_ids = count(0)
    
    def __init__(self, model=None, V0=None, theta0=None, shunt_z=(), shunt_y=(), name=None):
        if model is None:
            model = Model()

        elif isinstance(model, Model) is False:
            raise TypeError('provided model must an instance of the Model type or a subclass thereof')
            
        self.model = model

        if V0 is None:
            V0 = 1
        if theta0 is None:
            theta0 = 0

        _, _ = self.set_initial_voltage_polar((V0, theta0))

        self._bus_id = self._bus_ids.next() + 1
                
        self.shunt_y = impedance_admittance_wrangler(shunt_z, shunt_y)
        
        self.model.set_get_bus_polar_voltage_method(self.get_current_voltage_polar)
        self.model.set_update_bus_polar_voltage_method(self.update_voltage_polar)
        
        set_initial_conditions(self, 'w', 0)
        
        self.name = name


    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])


    def __contains__(self, model):
        if isinstance(model, Model) is True:
            return model is self.model
        
        return False


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
        
        return object_info

        
    def get_id(self):
        return self._bus_id


    def set_get_connected_bus_polar_voltage_from_network_method(self, method):
        self.get_connected_bus_polar_voltage_from_network_method = method
        self.model.set_get_connected_bus_polar_voltage_from_network_method(self.get_connected_bus_polar_voltage_from_network)


    def get_connected_bus_polar_voltage_from_network(self):
        return self.get_connected_bus_polar_voltage_from_network_method(bus_id=self._bus_id)


    def set_get_connected_bus_admittance_from_network_method(self, method):
        self.get_connected_bus_admittance_from_network_method = method
        self.model.set_get_connected_bus_admittance_from_network_method(self.get_connected_bus_admittance_from_network)


    def get_connected_bus_admittance_from_network(self):
        return self.get_connected_bus_admittance_from_network_method(self._bus_id)


    def set_get_apparent_power_injected_from_network_method(self, method):
        self.get_apparent_power_injected_from_network_method = method
        self.model.set_get_apparent_power_injected_from_network(self.get_apparent_power_injected_from_network)


    def get_apparent_power_injected_from_network(self):
        return self.get_apparent_power_injected_from_network_method(self)
        
        
    def prepare_for_dynamic_simulation_initial_value_calculation(self):
        return self.model.prepare_for_dynamic_simulation_initial_value_calculation()


    def prepare_for_dynamic_simulation(self):
        self.model.prepare_for_dynamic_simulation()


    def initialize_dynamic_states(self):
        self.model.initialize_dynamic_states()
        
    
    def prepare_for_dynamic_state_update(self):
        self.model.prepare_for_dynamic_state_update()


    def get_current_dynamic_state_array(self):
        return self.model.get_current_dynamic_state_array()


    def get_dynamic_state_time_derivative_array(self, current_states=None):
        return self.model.get_dynamic_state_time_derivative_array(current_states=current_states)


    def get_apparent_power_derivatives(self):
        return self.model.get_apparent_power_derivatives()


    def get_current_dynamic_angular_velocity(self):
        return self.model.get_current_dynamic_angular_velocity()


    def set_reference_dynamic_angular_velocity(self, reference_velocity):
        if reference_velocity is None:
            pass
        else:
            return self.model.set_reference_dynamic_angular_velocity(reference_velocity)


    def save_new_dynamic_state_array(self, new_state_array):
        self.model.save_new_dynamic_state_array(new_state_array)


    def get_dynamic_damping_coefficient(self):
        return self.model.get_dynamic_damping_coefficient()


    def get_dynamic_model_real_power_setpoint(self):
        return self.model.get_dynamic_model_real_power_setpoint()


    def change_dynamic_model_real_power_setpoint(self, new_setpoint):
        self.model.change_dynamic_model_real_power_setpoint(new_setpoint)


    def add_to_shunt_impedance(self, shunt_z=(), shunt_y=()):
        shunt_y_to_add = impedance_admittance_wrangler(shunt_z, shunt_y)
        previous_shunt_y = self.shunt_y
        self.shunt_y = (shunt_y_to_add[0]+previous_shunt_y[0], shunt_y_to_add[1]+previous_shunt_y[1])
        return self.shunt_y


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
        
        if V is not None:
            Vout = self.update_voltage_magnitude(V, replace=replace)
        else:
            Vout = self.get_current_voltage_magnitude()
        if theta is not None:
            thetaOut = self.update_voltage_angle(theta, replace=replace)
        else:
            thetaOut = self.get_current_voltage_angle()
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
        self.is_voltage_polar_static_old = self.is_voltage_polar_static()
        v_static, theta_static = self.model.make_voltage_polar_static()
        if v_static is not True and theta_static is not True:
            raise ModelError('cannot change static flags for model')


    def unmake_slack_bus(self):
        self.restore_is_voltage_polar_static()


    def restore_is_voltage_polar_static(self):
        try:
            v_static_old, theta_static_old = self.is_voltage_polar_static_old
        except AttributeError:
            debug('cannot restore is_voltage_polar_static, no previous values available')
        
        if v_static_old is True:
            self.model.make_voltage_magnitude_static()
        else:
            self.model.unmake_voltage_magnitude_static()
            
        if theta_static_old is True:
            self.model.make_voltage_angle_static()
        else:
            self.model.unmake_voltage_angle_static()
        
        v_static, theta_static = self.is_voltage_polar_static()
        if v_static != v_static_old or theta_static != theta_static_old:
            raise BusError('could not restore is_voltage_polar_static')
        

    def has_dynamic_model(self):
        return self.model.is_dynamic


    def has_generator_model(self):
        return self.model.is_generator


    def has_load_model(self):
        return self.model.is_load


    def get_apparent_power_injection(self):
        return self.model.get_apparent_power_injection()


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
