from itertools import count
from logging import debug, info, warning

from numpy import zeros

from ...exceptions import ModelError
from IPython import embed

class Model(object):
    _model_ids = count(0)
    
    def __init__(self, voltage_magnitude_static=False, voltage_angle_static=False,
					   is_dynamic=False, is_generator=False, is_load=False):
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


        if check_boolean_parameter(is_generator) is True:
            self.is_generator = is_generator
		
        if check_boolean_parameter(is_load) is True:
            self.is_load = is_load
            
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

