from inspect import currentframe, getargvalues
from logging import debug, info, warning
from math import sin
from operator import itemgetter

from numpy import append, array, empty, nan, nditer, zeros, hstack

from dynamic_model import DynamicModel
from microgrid_model.exceptions import ModelError
from microgrid_model.helper_functions import set_initial_conditions, set_parameter_value


class KuramotoOscillatorModel(DynamicModel):
    
    def __init__(self, parameters, initial_setpoint, is_generator=True, is_load=False):

        DynamicModel.__init__(self, voltage_magnitude_static=True, voltage_angle_static=False,
									is_generator=is_generator, is_load=is_load)
                 
        self.model_type = {
            'simple_name':'kuramoto_oscillator',
            'full_name':'Kuramoto Oscillator Dynamic Model'
        }

        # TO DO: get reasonable defaults for machine params
        self.parameter_defaults = {
            'D' : 0.1,
			'u_min' : 0.,
			'u_max' : 1.
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


    def get_limits(self):
        return self.u_min, self.u_max


    def _get_damping_coefficient(self):
        return self.D


    def _prepare_for_initial_value_calculation(self):
        self.initial_value_state = True


    def _prepare_for_state_update(self):
        connected_bus_angles = []
        for _, theta in self.get_connected_bus_polar_voltage_from_network():
            connected_bus_angles.append(theta)
        
        self.connected_bus_angles = connected_bus_angles
        
        admittances = self.get_connected_bus_admittance_from_network()
        # self.conductances = [y[0] for y in admittances]
        self.susceptances = [y[1] for y in admittances]


    def _initialize_states(self):
        # initial torque angle is whatever the voltage angle is for the bus
        _, theta = self.get_polar_voltage_from_bus()
        set_initial_conditions(self, 'd', theta)


    def _prepare_for_simulation(self):
        self.initial_value_state = False


    def _get_internal_voltage_angle(self):
        try:
            d = self.d[-1]
        except AttributeError, IndexError:
            debug('Could not get current torque angle, defaulting to NAN.')
            d = nan

        return d


    def _shift_internal_voltage_angle(self, _):
        pass


    def _get_real_power_injection(self, current_states=None):
        u = self._get_current_setpoint_array()[0]

        if self.initial_value_state is True:
            return u
        else:
            dd_dt = self.__dd_dt_model()
            return u - dd_dt*self.D


    def _get_reactive_power_injection(self, current_states=None):
        return 0


    def _get_state_time_derivative_array(self, current_states=None, current_setpoints=None):
        dd_dt = self.__dd_dt_model(current_states=current_states, current_setpoints=current_setpoints)
        return hstack((array([dd_dt]), zeros(len(self.connected_bus_angles))))


    def _save_new_state_array(self, new_state_array):
        d = self.__parse_state_array(new_state_array)
        self.d = append(self.d, d)
        self.update_bus_polar_voltage((None, d), replace=False)
        # return array([d])
        
        
    def __parse_state_array(self, state_array):
        return state_array[0]
            
    
    def _get_current_state_array(self):
        try:
            connected_bus_angles = self.connected_bus_angles
        except:
            connected_bus_angles = []
        angles = [self._get_internal_voltage_angle()]
        angles.extend(connected_bus_angles)
            
        return array(angles)


    def _save_new_setpoint_array(self, new_setpoints):
        u = self.__parse_setpoint_array(new_setpoints)
        self.u = append(self.u, u)
        if self._get_current_setpoint_array() != new_setpoints:
            raise ModelError('there was an error saving new setpoint array')


    def _get_real_power_setpoint(self):
        return self._get_current_setpoint_array()[0]


    def _change_real_power_setpoint(self, new_setpoint):
        self._save_new_setpoint_array(array([new_setpoint]))


    def __parse_setpoint_array(self, setpoint_array):
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


    def __dd_dt_model(self, current_states=None, current_setpoints=None):
        if current_setpoints is None:
            u = self._get_current_setpoint_array()[0]
        else:
            u = self.__parse_setpoint_array(current_setpoints)

        if current_states is None:
            current_states = self._get_current_state_array()

        theta_i = current_states[0]

        network_flow = 0
        for theta_j, Bij in nditer([current_states[1:], self.susceptances]):
            network_flow -= Bij*sin(theta_i - theta_j)

        return (u - network_flow)/self.D
        