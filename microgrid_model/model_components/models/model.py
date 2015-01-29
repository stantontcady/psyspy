from itertools import count
from logging import debug, info, warning

from microgrid_model.exceptions import ModelError

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


    def get_apparent_power_injection(self, Vpolar):
        try:
            P = self._get_real_power_injection(Vpolar)
        except AttributeError:
            debug('Could not get real power for model %i, defaulting to P=0' % (self._model_id))
            P = 0
        
        try:
            Q = self._get_reactive_power_injection(Vpolar)
        except AttributeError:
            debug('Could not get real power for model %i, defaulting to Q=0' % (self._model_id))
            Q = 0
            
        return P, Q

        
    def get_apparent_power_derivatives(self, Vpolar):
        try:
            dP_dtheta = self._dP_dtheta_model(Vpolar)
        except AttributeError:
            debug('Could not derivative of real power wrt voltage angle for model %i, defaulting to dP_dtheta=0' % (self._model_id))
            dP_dtheta = 0
        
        try:
            dP_dV = self._dP_dV_model(Vpolar)
        except AttributeError:
            debug('Could not derivative of real power wrt voltage magnitude for model %i, defaulting to dP_dV=0' % (self._model_id))
            dP_dV = 0
            
        try:
            dQ_dtheta = self._dQ_dtheta_model(Vpolar)
        except AttributeError:
            debug('Could not derivative of reactive power wrt voltage angle for model %i, defaulting to dQ_dtheta=0' % (self._model_id))
            dQ_dtheta = 0
        
        try:
            dQ_dV = self._dQ_dV_model(Vpolar)
        except AttributeError:
            debug('Could not derivative of reactive power wrt voltage magnitude for model %i, defaulting to dQ_dV=0' % (self._model_id))
            dQ_dV = 0

        return dP_dtheta, dP_dV, dQ_dtheta, dQ_dV


    def prepare_for_dynamic_simulation_initial_value_calculation(self):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot prepare for dynamic simulation initial value calculation' % (self._model_id))
            pass
        else:
            try:
                return self.prepare_for_initial_value_calculation()
            except ModelError:
                raise ModelError('model %i does not expose a method for preparing for initial value calculation' % (self._model_id))


    def initialize_dynamic_states(self, Vpolar, Snetwork):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot initialize dynamic states' % (self._model_id))
            pass
        else:
            try:
                return self.initialize_states(Vpolar, Snetwork)
            except ModelError:
                raise ModelError('model %i does not expose a method for getting dynamic state time derivatives' % (self._model_id))


    def get_dynamic_internal_voltage_angle(self):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot shift internal voltage angle' % (self._model_id))
            return None
        else:
            try:
                return self.get_internal_voltage_angle()
            except ModelError:
                raise ModelError('model %i does not expose a method for getting dynamic internal voltage angle' % (self._model_id))


    def shift_dynamic_internal_voltage_angle(self, angle_to_shift):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot shift internal voltage angle' % (self._model_id))
            pass
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
                return self.set_reference_angular_velocity(reference_velocity)
            except ModelError:
                debug('Model %i does not expose a method for setting the reference angular velocity' % (self._model_id))
                pass


    def save_bus_voltage_polar(self, Vpolar):
        try:
            return self._save_bus_voltage_polar(Vpolar)
        except AttributeError:
            debug('Model %i does not expose a method for saving the bus polar voltage, saving to member variable Vpolar' % (self._model_id))
            self.Vpolar = Vpolar
            pass
            

    def prepare_for_dynamic_simulation(self):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot prepare for dynamic simulation' % (self._model_id))
            pass
        else:
            try:
                return self.prepare_for_simulation()
            except ModelError:
                debug('Could not prepare model %i for dynamic simulation, no action taken' % (self._model_id))
                pass


    # def get_current_dynamic_state_array(self):
    #     if self.is_dynamic is False:
    #         debug('Model %i is not dynamic, cannot get dynamic state array' % (self._model_id))
    #         return None
    #     else:
    #         try:
    #             return self.get_state_time_derivative_array(Vpolar)
    #         except ModelError:
    #             raise ModelError('model %i does not expose a method for getting dynamic state time derivatives' % (self._model_id))
    #
    #
    # def get_dynamic_state_time_derivative_array(self, Vpolar):
    #     if self.is_dynamic is False:
    #         debug('Model %i is not dynamic, cannot get time derivative array' % (self._model_id))
    #         return None
    #     else:
    #         try:
    #             return self.get_state_time_derivative_array(Vpolar)
    #         except ModelError:
    #             raise ModelError('model %i does not expose a method for getting dynamic state time derivatives' % (self._model_id))


    def update_dynamic_states(self, numerical_integration_method):
        if self.is_dynamic is False:
            debug('Model %i is not dynamic, cannot update dynamic states' % (self._model_id))
            pass
        else:
            try:
                return self.update_states(numerical_integration_method)
            except ModelError:
                raise ModelError('model %i does not expose a method for updating the dynamic states' % (self._model_id))


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