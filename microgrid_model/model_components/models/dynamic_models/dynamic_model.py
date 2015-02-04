from logging import debug

from ..model import Model
from microgrid_model.exceptions import ModelError


class DynamicModel(Model):
    
    def __init__(self, voltage_magnitude_static=False, voltage_angle_static=False, is_generator=False):
        
        Model.__init__(self, voltage_magnitude_static=voltage_magnitude_static, voltage_angle_static=voltage_angle_static,
                             is_dynamic=True, is_generator=is_generator)
        
        
    def prepare_for_initial_value_calculation(self):
        try:
            self._prepare_for_initial_value_calculation()
        except AttributeError:
            debug('dynamic model %i does not have a member function for preparing for initial value calculation' % (self._model_id))
            pass


    def initialize_states(self):
        try:
            self._initialize_states()
        except AttributeError:
            raise AttributeError('dynamic model %i does not have a member function for initializing states' % (self._model_id))
            

    def get_internal_voltage_angle(self):
        try:
            return self._get_internal_voltage_angle()
        except AttributeError:
            raise AttributeError('dynamic model %i does not have a member function for getting internal voltage angle' % (self._model_id))


    def get_current_angular_velocity(self):
        try:
            return self._get_current_angular_velocity()
        except AttributeError:
            debug('dynamic model %i does not have a member function for getting the current angular velocity' % (self._model_id))
            return None


    def set_reference_angular_velocity(self, reference_velocity):
        try:
            self._set_reference_angular_velocity(reference_velocity)
        except AttributeError:
            debug('dynamic model %i does not have a member function for setting the reference angular velocity' % (self._model_id))
            pass


    def shift_internal_voltage_angle(self, angle_to_shift):
        try:
            return self._shift_internal_voltage_angle(angle_to_shift)
        except AttributeError:
            debug('dynamic model %i does not have a member function for shifting internal voltage angle' % (self._model_id))
            pass


    def prepare_for_simulation(self):
        try:
            self._prepare_for_simulation()
        except AttributeError:
            debug('dynamic model %i does not have a member function for getting the state time derivative array' % (self._model_id))
            pass


    def prepare_for_state_update(self):
        try:
            self._prepare_for_state_update()
        except AttributeError:
            debug('dynamic model %i does not have a member function to prepare for dynamic state update' % (self._model_id))
            pass


    def get_current_state_array(self):
        try:
            return self._get_current_state_array()
        except AttributeError:
            raise AttributeError('dynamic model %i does not have a member function for getting current states' % (self._model_id))


    def get_state_time_derivative_array(self, current_states=None):
        try:
            return self._get_state_time_derivative_array(current_states=current_states)
        except AttributeError:
            raise AttributeError('dynamic model %i does not have a member function for getting state time derivative array' % (self._model_id))


    def save_new_state_array(self, new_state_array):
        try:
            self._save_new_state_array(new_state_array)
        except AttributeError:
            raise AttributeError('dynamic model %i does not have a member function for saving new state array' % (self._model_id))

    # def update_states(self, numerical_integration_method):
    #     try:
    #         current_states = self._get_current_state_array()
    #     except AttributeError:
    #         raise AttributeError('dynamic model %i does not have a member function for getting current states' % (self._model_id))
    #
    #     try:
    #         get_time_derivative_method = self._get_state_time_derivative_array
    #     except AttributeError:
    #         raise AttributeError('dynamic model %i does not have a member function for getting state time derivative array' % (self._model_id))
    #
    #     try:
    #         save_new_states_method = self._save_new_state_array
    #     except AttributeError:
    #         raise AttributeError('dynamic model %i does not have a member function for saving new state array' % (self._model_id))
    #
    #     updated_states = numerical_integration_method(current_states, get_time_derivative_method)
    #     save_new_states_method(updated_states)
