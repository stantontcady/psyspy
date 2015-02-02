from inspect import currentframe, getargvalues
from logging import debug, info, warning
from math import asin, atan, cos, pi, sin, sqrt
from operator import itemgetter

from numpy import append, array, empty, nan

from dynamic_model import DynamicModel
from microgrid_model.exceptions import ModelError
from microgrid_model.model_components.helper_functions import set_initial_conditions, set_parameter_value


class KuramotoOscillatorModel(DynamicModel):
    
    def __init__(self, parameters, initial_setpoint, is_generator=True):
                 
        DynamicModel.__init__(self, voltage_magnitude_static=True, voltage_angle_static=False, is_generator=is_generator)
                 
        self.model_type = {
            'simple_name':'kuramoto_oscillator',
            'full_name':'Kuramoto Oscillator Dynamic Model'
        }

        # TO DO: get reasonable defaults for machine params
        self.parameter_defaults = {
            'D' : 0.1
        }
        
        for parameter, default_value in self.parameter_defaults.iteritems():
            try:
                value = parameters[parameter]
            except KeyError:
                value = default_value

            set_parameter_value(self, parameter, value)

        set_initial_conditions(self, 'u', initial_setpoint)


    def repr_helper(self, simple=False, indent_level_increment=2):
        if self.is_generator is True:
            gen_or_load = 'Generator'
        else:
            gen_or_load = 'Load'
        object_info = ['<%s: %s>' % (self.model_type['full_name'], gen_or_load)]
        current_states = []
        parameters = []
        
        if simple is False:
            parameters.append('Damping coefficient, D: %0.3f' % (self.D))
        
        current_states.append('Torque angle, %s : %0.3f' % (u'\u03B4'.encode('UTF-8'), self.d[-1]))
        current_states.append('Set-point, u: %0.3f' % (self.u[-1]))
        
        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
            
        return object_info

        
    def _prepare_for_initial_value_calculation(self):
        pass


    def _prepare_for_simulation(self):
        pass


    def _initialize_states(self, Vpolar, Snetwork):
        d0 = Vpolar[1]
        set_initial_conditions(self, 'd', d0)


    def _get_internal_voltage_angle(self):
        d = self._get_current_state_array()[0]
        return d


    def _get_real_power_injection(self, current_states=None):
        u = self._get_current_setpoint_array()[0]
        try:
            Pnetwork, _ = self.Snetwork
        except AttributeError:
            Pnetwork = None

        if Pnetwork is None:
            return u
        else:
            dd_dt = self._dd_dt_model(Pnetwork)
            return u - dd_dt*self.D


    def _get_reactive_power_injection(self, Vpolar, current_states=None):
        return 0
        
    
    # def _save_apparent_power_injected_from_network(self, Snetwork, k):
    #     self.Snetwork = Snetwork
    #     # last iteration Snetwork was received
    #     self.snetwork_k = k


    # def _update_states(self, numerical_integration_method):
    #     current_states = self._get_current_state_array()
    #     updated_states = numerical_integration_method(current_states, self._get_state_time_derivative_array)
    #     self._save_new_state_array(updated_states)


    def _get_state_time_derivative_array(self, current_states=None, current_setpoints=None):
        try:
            Pnetwork, _ = self.Snetwork
        except AttributeError:
            raise AttributeError('cannot get time derivative array for model %i, no member variable called Snetwork' % (self._model_id))

        dd_dt = self._dd_dt_model(Pnetwork, current_states=current_states)
        return array([dd_dt])


    def _save_new_state_array(self, new_states):
        d = self._parse_state_array(new_states)
        self.d = append(self.d, d)
        return self._get_current_state_array()
        
        
    def _parse_state_array(self, state_array):
        if state_array.ndim != 1 and len(state_array) != 1:
            raise ModelError('state array is the wrong dimension or size')
        
        try:
            d = state_array
        except IndexError:
            raise IndexError('state array does not have 1 element')
        
        return d
            
    
    def _get_current_state_array(self):
        try:
            d = self.d[-1]
        except AttributeError, IndexError:
            debug('Could not get current torque angle, defaulting to NAN.')
            d = nan
            
        return array([d])


    def _save_new_setpoint_array(self, new_setpoints):
        u = self._parse_setpoint_array(new_setpoints)
        self.u = append(self.u, u)
        return self._get_current_state_array()


    def _parse_setpoint_array(self, setpoint_array):
        if setpoint_array.ndim != 1 and len(setpoint_array) != 1:
            raise ModelError('setpoint array is the wrong dimension or size')
        
        try:
            u = setpoint_array[0]
        except IndexError:
            raise ModelError('setpoint array does not have 1 element')
        
        return u
            
    
    def _get_current_setpoint_array(self):
        try:
            u = self.u[-1]
        except AttributeError, IndexError:
            debug('Could not get current governor setpoint, defaulting to NAN.')
            u = nan
            
        return array([u])


    def _dd_dt_model(self, Pnetwork, current_states=None, current_setpoints=None):
        if current_setpoints is None:
            u = self._get_current_setpoint_array()[0]
        else:
            u = self._parse_state_array(current_setpoints)
        return (u - Pnetwork)/self.D
        