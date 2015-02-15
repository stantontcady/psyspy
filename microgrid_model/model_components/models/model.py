from itertools import count
from logging import debug, info, warning

from numpy import zeros

from microgrid_model.exceptions import ModelError
from IPython import embed

class Model(object):
    _model_ids = count(0)
    
    def __init__(self, voltage_magnitude_static=False, voltage_angle_static=False, is_dynamic=False, is_generator=False):
        self._model_id = self._model_ids.next() + 1
        
        def check_boolean_parameter(parameter):
            if parameter is True or parameter is False:
                return True
            else:
                raise ModelError('%s must be boolean' % (parameter))

        if check_boolean_parameter(voltage_magnitude_static) is True:
            self.voltage_magnitude_static = voltage_magnitude_static
        
        if check_boolean_parameter(voltage_angle_static) is True:
            self.voltage_angle_static = voltage_angle_static

        if check_boolean_parameter(is_dynamic) is True:
            self.is_dynamic = is_dynamic

        if check_boolean_parameter(is_generator) is True:
            self.is_generator = is_generator
            
        self._get_bus_polar_voltage_method = None
        self._get_apparent_power_injected_by_network_method = None
        self._get_polar_voltage_of_connected_buses_method = None
        self._setpoint_change_time = zeros(1)


    def __repr__(self):
        try:
            return '\n'.join([line for line in self.repr_helper()])
        except AttributeError:
            try:
                model_name = self.model_type['full_name']
            except AttributeError:
                return '<Model %i>' % self._model_id


    def set_update_bus_polar_voltage_method(self, method):
        self._update_bus_polar_voltage_method = method


    def update_bus_polar_voltage(self, Vpolar, replace=False):
        update_method = self._get_method_from_parent_object('_update_bus_polar_voltage_method',
                                                            'method for updating polar bus voltage has not been set',
                                                            'method for updating polar bus voltage is not callable')
        update_method(Vpolar, replace=replace)


    def set_get_bus_polar_voltage_method(self, method):
        self._get_bus_polar_voltage_method = method


    def get_polar_voltage_from_bus(self):
        return self._call_method_from_parent_object('_get_bus_polar_voltage_method',
                                                    'method for getting polar voltage from bus has not been set',
                                                    'method for getting polar voltage from bus is not callable')


    def set_get_apparent_power_injected_from_network(self, method):
        self._get_apparent_power_injected_by_network_method = method


    def get_apparent_power_injected_from_network(self):
        return self._call_method_from_parent_object('_get_apparent_power_injected_by_network_method',
                                                    'method for getting apparent power from network has not been set',
                                                    'method for getting apparent power from network is not callable')


    def set_get_connected_bus_admittance_from_network_method(self, method):
        self._get_connected_bus_admittance_from_network_method = method


    def get_connected_bus_admittance_from_network(self):
        return self._call_method_from_parent_object('_get_connected_bus_admittance_from_network_method',
                                                    'method for getting connected bus admittance from network has not been set',
                                                    'method for getting connected bus admittance from network is not callable')


    def set_get_connected_bus_polar_voltage_from_network_method(self, method):
        self._get_connected_bus_polar_voltage_from_network_method = method


    def get_connected_bus_polar_voltage_from_network(self):
        return self._call_method_from_parent_object('_get_connected_bus_polar_voltage_from_network_method',
                                                    'method for getting polar voltage of connected buses from network has not been set',
                                                    'method for getting polar voltage of connected buses from network is not callable')


    def _call_method_from_parent_object(self, method, attribute_error_message, callable_error_message):
        parent_method = self._get_method_from_parent_object(method, attribute_error_message, callable_error_message)
        return parent_method()


    def _get_method_from_parent_object(self, method_name, attribute_error_message, callable_error_message):
        if hasattr(self, method_name) is True:
            method = getattr(self, method_name)
        else:
            raise AttributeError(attribute_error_message)

        if hasattr(method, '__call__') is True:
            return method
        else:
            raise TypeError(callable_error_message)


    def _get_dynamic_model_method(self, method_name):
        if self.is_dynamic is False:
            return None
        elif hasattr(self, method_name):
            method = getattr(self, method_name)
            if hasattr(method, '__call__'):
                return method

        raise False


    def get_apparent_power_injection(self):
        try:
            P = self._get_real_power_injection()
        except AttributeError:
            debug('Could not get real power for model %i, defaulting to P=0' % (self._model_id))
            P = 0
        
        try:
            Q = self._get_reactive_power_injection()
        except AttributeError:
            debug('Could not get real power for model %i, defaulting to Q=0' % (self._model_id))
            Q = 0

        return P, Q

        
    def get_apparent_power_derivatives(self):
        try:
            dP_dtheta = self._dP_dtheta_model()
        except AttributeError:
            debug('Could not derivative of real power wrt voltage angle for model %i, defaulting to dP_dtheta=0' % (self._model_id))
            dP_dtheta = 0
        
        try:
            dP_dV = self._dP_dV_model()
        except AttributeError:
            debug('Could not derivative of real power wrt voltage magnitude for model %i, defaulting to dP_dV=0' % (self._model_id))
            dP_dV = 0
            
        try:
            dQ_dtheta = self._dQ_dtheta_model()
        except AttributeError:
            debug('Could not derivative of reactive power wrt voltage angle for model %i, defaulting to dQ_dtheta=0' % (self._model_id))
            dQ_dtheta = 0
        
        try:
            dQ_dV = self._dQ_dV_model()
        except AttributeError:
            debug('Could not derivative of reactive power wrt voltage magnitude for model %i, defaulting to dQ_dV=0' % (self._model_id))
            dQ_dV = 0

        return dP_dtheta, dP_dV, dQ_dtheta, dQ_dV


    def prepare_for_dynamic_simulation_initial_value_calculation(self):
        method = self._get_dynamic_model_method('prepare_for_initial_value_calculation')
        if method is None:
            debug('Model %i is not dynamic, cannot prepare for dynamic simulation initial value calculation' % (self._model_id))
        elif method is False:
            debug('Model %i does not expose a method for preparing for initial value calculation' % (self._model_id))
        else:
            method()
        
        pass


    def initialize_dynamic_states(self):
        method = self._get_dynamic_model_method('initialize_states')
        if method is None:
            debug('Model %i is not dynamic, cannot initialize dynamic states' % (self._model_id))
            pass
        elif method is False:
            raise ModelError('model %i does not expose a method for getting dynamic state time derivatives' % (self._model_id))
        else:
            method()


    def get_dynamic_internal_voltage_angle(self):
        method = self._get_dynamic_model_method('get_internal_voltage_angle')
        if method is None:
            debug('Model %i is not dynamic, cannot shift internal voltage angle' % (self._model_id))
            return None
        elif method is False:
            raise ModelError('model %i does not expose a method for getting dynamic internal voltage angle' % (self._model_id))
        else:
            return method()                


    def shift_dynamic_internal_voltage_angle(self, angle_to_shift):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot shift internal voltage angle' % (self._model_id))
            return None
        else:
            try:
                return self.shift_internal_voltage_angle(angle_to_shift)
            except ModelError:
                raise ModelError('model %i does not expose a method for shifting dynamic internal voltage angle' % (self._model_id))


    def get_current_dynamic_angular_velocity(self):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot retrieve current angular velocity' % (self._model_id))
            return None
        else:
            try:
                return self.get_current_angular_velocity()
            except ModelError:
                raise ModelError('model %i does not expose a method for retrieving the current angular velocity' % (self._model_id))


    def set_reference_dynamic_angular_velocity(self, reference_velocity):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot set reference angular velocity' % (self._model_id))
            pass
        else:
            try:
                self.set_reference_angular_velocity(reference_velocity)
            except ModelError:
                debug('Model %i does not expose a method for setting the reference angular velocity' % (self._model_id))
                pass


    def prepare_for_dynamic_simulation(self):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot prepare for dynamic simulation' % (self._model_id))
            pass
        else:
            try:
                self.prepare_for_simulation()
            except ModelError:
                debug('Could not prepare model %i for dynamic simulation, no action taken' % (self._model_id))
                pass


    def prepare_for_dynamic_state_update(self):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot prepare dynamic state update' % (self._model_id))
            pass
        else:
            try:
                self.prepare_for_state_update()
            except ModelError:
                raise ModelError('model %i does not expose a method to prepare for dynamic state update' % (self._model_id))


    def get_current_dynamic_state_array(self):
        method = self._get_dynamic_model_method('get_current_state_array')
        if method is None:
            debug('Model %i is not dynamic, cannot get current dynamic states' % (self._model_id))
            return None
        elif method is False:
            raise ModelError('model %i does not expose a method for getting current dynamic states' % (self._model_id))
        else:
            return method()


    def get_dynamic_state_time_derivative_array(self, current_states=None):
        method = self._get_dynamic_model_method('get_state_time_derivative_array')
        if method is None:
            debug('Model %i is not dynamic, cannot get dynamic state time derivative array' % (self._model_id))
            return None
        elif method is False:
            raise ModelError('model %i does not expose a method for getting dynamic state time derivative array' % (self._model_id))
        else:
            return method(current_states=current_states)


    def save_new_dynamic_state_array(self, new_state_array):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot save new dynamic state array' % (self._model_id))
            pass
        else:
            try:
                self.save_new_state_array(new_state_array)
            except ModelError:
                raise ModelError('model %i does not expose a method for saving new state array' % (self._model_id))


    def get_dynamic_damping_coefficient(self):
        method = self._get_dynamic_model_method('get_damping_coefficient')
        if method is None:
            debug('Model %i is not dynamic, cannot get dynamic damping coefficient' % (self._model_id))
        elif method is False:
            debug('model %i does not expose a method for getting dynamic damping coefficient' % (self._model_id))
        else:
            return method()
        return None


    def get_dynamic_model_real_power_setpoint(self):
        method = self._get_dynamic_model_method('get_real_power_setpoint')
        if method is None:
            debug('Model %i is not dynamic, cannot get real power setpoint' % (self._model_id))
        elif method is False:
            debug('model %i does not expose a method for getting real power setpoint' % (self._model_id))
        else:
            return method()
        return None


    def change_dynamic_model_real_power_setpoint(self, new_setpoint):
        method = self._get_dynamic_model_method('change_real_power_setpoint')
        if method is None:
            debug('Model %i is not dynamic, cannot change real power setpoint' % (self._model_id))
        elif method is False:
            debug('model %i does not expose a method for changing real power setpoint' % (self._model_id))
        else:
            method(new_setpoint)
        pass


    def is_voltage_polar_static(self):
        return self.is_voltage_magnitude_static(), self.is_voltage_angle_static()


    def is_voltage_magnitude_static(self):
        return self.voltage_magnitude_static


    def is_voltage_angle_static(self):
        return self.voltage_angle_static


    def make_voltage_polar_static(self):
        return self.make_voltage_magnitude_static(), self.make_voltage_angle_static()


    def make_voltage_magnitude_static(self):
        self.voltage_magnitude_static = True
        return self.is_voltage_magnitude_static()


    def make_voltage_angle_static(self):
        self.voltage_angle_static = True
        return self.is_voltage_angle_static()


    def unmake_voltage_polar_static(self):
        return self.unmake_voltage_magnitude_static(), self.unmake_voltage_angle_static()


    def unmake_voltage_magnitude_static(self):
        self.voltage_magnitude_static = False
        return self.is_voltage_magnitude_static()


    def unmake_voltage_angle_static(self):
        self.voltage_angle_static = False
        return self.is_voltage_angle_static()
