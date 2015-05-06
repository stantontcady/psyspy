from inspect import currentframe, getargvalues
from logging import debug, info, warning
from math import asin, atan, cos, pi, sin, sqrt
from operator import itemgetter

from numpy import append, array, empty, nan

from dynamic_model import DynamicModel
from microgrid_model.exceptions import ModelError
from microgrid_model.helper_functions import set_initial_conditions, set_parameter_value


class StructurePreservingSynchronousGeneratorModel(DynamicModel):
    
    def __init__(self, parameters, initial_setpoint):
                 
        DynamicModel.__init__(self,
							  voltage_magnitude_static=False, voltage_angle_static=False,
							  is_generator=True, is_load=False)
                 
        self.model_type = {
            'simple_name':'structure_preserving',
            'full_name':'Structure-Preserving With Constant Voltage Behind Reactance Generator Model'
        }

        # TO DO: get reasonable defaults for machine params
        self.parameter_defaults = {
            'wnom' : 2*pi*60,
            'H': 1.,
            'M' : 1/(pi*60),
            'D' : 0.1,
            'taug' : 0.1,
            'Rd' : 1,
            'R' : 0,
            'Xdp' : 0.1
        }
        
        for parameter, default_value in self.parameter_defaults.iteritems():
            try:
                value = parameters[parameter]
            except KeyError:
                value = default_value

            set_parameter_value(self, parameter, value)

        set_initial_conditions(self, 'u', initial_setpoint)

        self.reference_angular_velocity = None


    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<%s>' % self.model_type['full_name']]
        current_states = []
        parameters = []
        
        if simple is False:
            parameters.append('Nominal frequency, %s_nom: %0.3f' % (u'\u03C9'.encode('UTF-8'), self.wnom))
            parameters.append('Moment of inertia, M: %0.3f' % (self.M))
            parameters.append('Damping coefficient, D: %0.3f' % (self.D))
            parameters.append('Governor time constant, %s_g: %0.3f' % (u'\u03C4'.encode('UTF-8'), self.taug))
            parameters.append('Droop coefficient, Rd: %0.3f' % (self.Rd))
            parameters.append('Generator resistance, R: %0.3f' % (self.R))
            parameters.append('Generator reactance, Xd\': %0.3f' % (self.Xdp))
        
        try:
            current_states.append('Back EMF, E: %0.3f' % (self.E[-1]))
        except AttributeError:
            pass

        current_states.append('Torque angle, %s : %0.3f' % (u'\u03B4'.encode('UTF-8'), self.d[-1]))
        current_states.append('Angular speed, %s : %0.3f' % (u'\u03C9'.encode('UTF-8'), self.w[-1]))
        current_states.append('Real power output, P: %0.3f' % (self.P[-1]))
        current_states.append('Set-point, u: %0.3f' % (self.u[-1]))
        
        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
            
        return object_info

        
    def _prepare_for_initial_value_calculation(self):
        # need to emulate a PV bus during initial value
        self.make_voltage_magnitude_static()


    def _initialize_states(self):
        d0, w0, P0 = self.__get_initial_state_array()
        set_initial_conditions(self, 'd', d0)
        set_initial_conditions(self, 'w', w0)
        set_initial_conditions(self, 'P', P0)


    def _shift_internal_voltage_angle(self, angle_to_shift):
        if len(self.d) > 1:
            raise ModelError('Cannot shift initial angle, size of angle array is larger than 1')
            return False
        current_angle = self.d[0]
        self.d = array([current_angle - angle_to_shift])
        return self.d[0]


    def _prepare_for_simulation(self):
        self.unmake_voltage_magnitude_static()


    def _get_internal_voltage_angle(self):
        d, _, _ = self._get_current_state_array()
        return d


    def _get_current_angular_velocity(self):
        _, w, _ = self._get_current_state_array()
        return w
        
    
    def _set_reference_angular_velocity(self, reference_velocity):
        self.reference_angular_velocity = reference_velocity


    def _get_real_power_injection(self, current_states=None):
        # voltage magnitude should only be static during initial value computation
        if self.is_voltage_magnitude_static() is True:
            return self._get_current_setpoint_array()[0]
        else:
            if current_states is None:
                d, _, _ = self._get_current_state_array()
            else:
                d, _, _ = self.__parse_state_array(current_states)

            return self.__p_out_model(d=d)


    def _get_reactive_power_injection(self, current_states=None):
        # voltage magnitude should only be static during initial value computation
        if self.is_voltage_magnitude_static() is True:
            return 0
        else:
            if current_states is not None:
                d, _, _ = self.__parse_state_array(current_states)
            else:
                d = None

            return self.__q_out_model(d=d)


    def _get_state_time_derivative_array(self, current_states=None, current_setpoints=None):
        if self.reference_angular_velocity is None:
            # if no reference angular velocity we assume this is the reference node
            wref = self.wnom
        else:
            wref = self.reference_angular_velocity

        Vpolar = self.get_polar_voltage_from_bus()

        dd_dt = self.__dd_dt_model(Vpolar, current_states=current_states, wref=wref)
        dw_dt = self.__dw_dt_model(Vpolar, current_states=current_states, wref=wref)
        dP_dt = self.__dP_dt_model(Vpolar, current_states=current_states, current_setpoints=current_setpoints, wref=wref)
        return array([dd_dt, dw_dt, dP_dt])


    def _save_new_state_array(self, new_states):
        d, w, P = self.__parse_state_array(new_states)
        self.d = append(self.d, d)
        self.w = append(self.w, w)
        self.P = append(self.P, P)
        return self._get_current_state_array()


    def __get_initial_state_array(self):
        Vpolar = self.get_polar_voltage_from_bus()
        Pnetwork, Qnetwork = self.get_apparent_power_injected_from_network()
        
        d0 = self.__d0_model(Vpolar, Pnetwork, Qnetwork)
        w0 = self.__w0_model()
        P0 = self.__P0_model(Pnetwork)
        
        return array([d0, w0, P0])
        
        
    def __parse_state_array(self, state_array):
        if state_array.ndim != 1 and len(state_array) != 3:
            raise ModelError('state array is the wrong dimension or size')
        
        try:
            d, w, P = state_array
        except IndexError:
            raise ModelError('state array does not have 3 elements')
        
        return d, w, P
            
    
    def _get_current_state_array(self):
        try:
            d = self.d[-1]
        except AttributeError, IndexError:
            debug('Could not get current torque angle, defaulting to NAN.')
            d = nan

        try:
            w = self.w[-1]
        except AttributeError, IndexError:
            debug('Could not get current angular velocity, defaulting to NAN.')
            w = nan
            
        try:
            P = self.P[-1]
        except AttributeError, IndexError:
            debug('Could not get current governor power value, defaulting to NAN.')
            P = nan
            
        return array([d, w, P])


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


    def __dd_dt_model(self, Vpolar, wref, current_states=None):
        if current_states is None:
            _, w, _ = self._get_current_state_array()
        else:
            _, w, _ = self.__parse_state_array(current_states)

        return w - wref

        
    def __d0_model(self, Vpolar, Pnetwork, Qnetwork):
        E, d = self.__back_emf_initial_value(Vpolar, Pnetwork, Qnetwork)
        # save back emf voltage magnitude here since it doesn't have a dynamic model in this generator model
        set_initial_conditions(self, 'E', E)
        return d


    def __dw_dt_model(self, Vpolar, wref, current_states=None):
        if current_states is None:
            d, w, P = self._get_current_state_array()
        else:
            d, w, P = self.__parse_state_array(current_states)

        Pout = self.__p_out_model(Vpolar=Vpolar, d=d)

        return (1./self.M)*(P - Pout - self.D*(w - wref))
        

    def __w0_model(self):
        return self.wnom

        
    def __dP_dt_model(self, Vpolar, wref, current_states=None, current_setpoints=None):
        if current_states is None:
            _, w, P = self._get_current_state_array()
        else:
            _, w, P = self.__parse_state_array(current_states)

        if current_setpoints is None:
            u = self._get_current_setpoint_array()[0]
        else:
            u = self.__parse_setpoint_array(current_setpoints)

        return (1./self.taug)*(u - P - (1./(self.Rd*wref))*(w - wref))


    def __P0_model(self, Pnetwork):
        return Pnetwork

        
    def __p_out_model(self, Vpolar=None, d=None):
        if d is None:
            d, _, _ = self._get_current_state_array()

        if Vpolar is None:
            Vpolar = self.get_polar_voltage_from_bus()
        V, theta = Vpolar

        return (1./self.Xdp)*self.E[-1]*V*sin(d - theta)
        
        
    def __q_out_model(self, Vpolar=None, d=None):
        if d is None:
            d, _, _ = self._get_current_state_array()
            
        if Vpolar is None:
            Vpolar = self.get_polar_voltage_from_bus()
        V, theta = Vpolar

        return (1./self.Xdp)*(self.E[-1]*V*cos(theta - d) - V**2)


    def _dP_dtheta_model(self, d=None):
        if d is None:
            d, _, _ = self._get_current_state_array()
        V, theta = self.get_polar_voltage_from_bus()
        return -1*(1./self.Xdp)*V*self.E[-1]*cos(d - theta)


    def _dP_dV_model(self, d=None):
        if d is None:
            d, _, _ = self._get_current_state_array()
        _, theta = self.get_polar_voltage_from_bus()
        return (1./self.Xdp)*self.E[-1]*sin(d - theta)
        
    
    # def dp_out_d_d_model(self, V, theta, d=None):
    #     if d is None:
    #         d, _, _ = self._get_current_state_array()
    #     return (1./self.Xdp)*V*self.E[-1]*cos(d - theta)


    def _dQ_dtheta_model(self, d=None):
        if d is None:
            d, _, _ = self._get_current_state_array()
        V, theta = self.get_polar_voltage_from_bus()
        return -1*(1./self.Xdp)*V*self.E[-1]*sin(theta - d)
        
        
    def _dQ_dV_model(self, d=None):
        if d is None:
            d, _, _ = self._get_current_state_array()
        V, theta = self.get_polar_voltage_from_bus()
        return (1./self.Xdp)*self.E[-1]*cos(theta - d) - 2*V/self.Xdp

        
    # def dq_out_d_d_model(self, V, theta, d=None):
    #     if d is None:
    #         d, _, _ = self.get_current_states()
    #     return (1./self.Xdp)*V*self.E[-1]*sin(theta - d)

        
    def __back_emf_initial_value(self, Vpolar, Pg, Qg):
        # DOES NOT INCLUDE GEN LOSSES
        # these are needed numerous times, compute once first
        V, theta = Vpolar
        cos_theta = cos(theta)
        sin_theta = sin(theta)
        # Back emf is E < delta = a + jb
        a = V*cos_theta + self.Xdp*(Qg*cos_theta - Pg*sin_theta)/V
        b = V*sin_theta + self.Xdp*(Pg*cos_theta + Qg*sin_theta)/V
        
        E = sqrt(a**2 + b**2)
        delta = atan(b/a)
        
        return E, delta
        