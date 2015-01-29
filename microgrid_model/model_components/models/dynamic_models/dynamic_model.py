

from ..model import Model
from microgrid_model.exceptions import ModelError


class DynamicModel(Model):
    
    def __init__(self, voltage_magnitude_static=False, voltage_angle_static=False, is_generator=False):
        
        Model.__init__(self, voltage_magnitude_static=False, voltage_angle_static=False,
                             is_dynamic=True, is_generator=False)
        
        
    def prepare_for_initial_value_calculation(self):
        try:
            return self._prepare_for_initial_value_calculation()
        except AttributeError:
            raise ModelError('dynamic model %i does not have a member function for preparing for initial value calculation' % (self._model_id))


    def initialize_states(self, Vpolar, Snetwork):
        try:
            return self._initialize_states(Vpolar, Snetwork)
        except AttributeError:
            raise ModelError('dynamic model %i does not have a member function for initializing states' % (self._model_id))
            

    def get_internal_voltage_angle(self):
        try:
            return self._get_internal_voltage_angle()
        except AttributeError:
            raise ModelError('dynamic model %i does not have a member function for getting internal voltage angle' % (self._model_id))


    def get_current_angular_velocity(self):
        try:
            return self._get_current_angular_velocity()
        except AttributeError:
            debug('dynamic model %i does not have a member function for getting the current angular velocity' % (self._model_id))
            return None


    def set_reference_angular_velocity(self, reference_velocity):
        try:
            return self._set_reference_angular_velocity(reference_velocity)
        except AttributeError:
            debug('dynamic model %i does not have a member function for setting the reference angular velocity' % (self._model_id))
            return None


    def shift_internal_voltage_angle(self, angle_to_shift):
        try:
            return self._shift_internal_voltage_angle(angle_to_shift)
        except AttributeError:
            raise ModelError('dynamic model %i does not have a member function for shifting internal voltage angle' % (self._model_id))


    def prepare_for_simulation(self):
        try:
            return self._prepare_for_simulation()
        except AttributeError:
            raise ModelError('dynamic model %i does not have a member function for getting the state time derivative array' % (self._model_id))


    def update_states(self, numerical_integration_method):
        try:
            return self._update_states(numerical_integration_method)
        except AttributeError:
            raise ModelError('dynamic model %i does not have a member function for updating states' % (self._model_id))
