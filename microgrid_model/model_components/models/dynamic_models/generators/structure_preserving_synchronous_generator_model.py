from inspect import currentframe, getargvalues
from logging import debug, info, warning
from math import asin, atan, cos, pi, sin, sqrt
from operator import itemgetter

from numpy import append, empty, nan

from ..dynamic_model import DynamicModel


class StructurePreservingSynchronousGeneratorModel(DynamicModel):
    
    def __init__(self,
                 wnom=None,
                 H=None,
                 M=None,
                 D=None,
                 taug=None,
                 Rd=None,
                 R=None,
                 Xdp=None,
                 E=None,
                 u=None):
                 
        self.model_type = {
            'simple_name':'structure_preserving',
            'full_name':'Structure-Preserving With Constant Voltage Behind Reactance'
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

        # _, _, _, arg_values = getargvalues(currentframe())
        #
        # GeneratorModel.__init__(self, arg_values)
        
        # INITIAL STATES
        # generator set-point
        set_initial_conditions(self, 'u', u)
        
    def repr_helper(self, simple=False, indent_level_increment=2):
        object_info = ['<%s DGR Model>' % self.model_type['full_name']]
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


    def _prepare_for_dynamic_simulation(self):
        self.unmake_voltage_magnitude_static()


    def _initialize_states(self, Vpolar, Snetwork):
        pass
        
    
    def _get_internal_voltage_angle(self):
        d, _, _ = self._get_current_state_array()
        return d


    def _get_real_power_injection(self, Vpolar, current_states=None):
        # voltage magnitude should only be static during initial value computation
        if self.is_voltage_magnitude_static() is True:
            return self._get_current_setpoint_array()[0]
        else:
            if current_states is None:
                d, _, _ = self._get_current_state_array()
            else:
                d, _, _ = self._parse_state_array(current_states)

            return self._p_out_model(Vpolar, d=d)


    def _get_reactive_power_injection(self, Vpolar, current_states=None):
        # voltage magnitude should only be static during initial value computation
        if self.is_voltage_magnitude_static() is True:
            return 0
        else:
            if current_states is None:
                d, _, _ = self._get_current_state_array()
            else:
                d, _, _ = self._parse_state_array(current_states)

            return self._q_out_model(Vpolar, d=d)


    def _get_state_time_derivative_array(self, Vpolar, current_states=None, current_setpoints=None):
        dd_dt = self._dd_dt_model(Vpolar, current_states=current_states)
        dw_dt = self._dw_dt_model(Vpolar, current_states=current_states)
        dP_dt = self._dP_dt_model(Vpolar, current_states=current_states, current_setpoints=current_setpoints)
        return array([dd_dt, dw_dt, dP_dt])
        
        
    def _get_initial_state_array(self, Vpolar, Snetwork):
        try:
            Pnetwork, Qnetwork = Snetwork
        except ValueError, TypeError:
            raise ModelError('could not unpack apparent power from network')
    
        d0 = self._d0_model(Vpolar, Pnetwork, Qnetwork)
        w0 = self._w0_model()
        P0 = self._P0_model(Pnetwork)
        
        return array([d0, w0, P0])
        
        
    def _parse_state_array(self, state_array):
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


    def _dd_dt_model(self, Vpolar, current_states=None):
        if current_states is None:
            _, w, _ = self._get_current_state_array()
        else:
            _, w, _ = self._parse_state_array(current_states)

        if wref is None:
            # if no reference angular velocity we assume this is the reference node
            wref = self.wnom

        return w - wref

        
    def _d0_model(self, Vpolar, Pnetwork, Qnetwork):
        E, d = self._back_emf_initial_value(Vpolar, Pnetwork, Qnetwork)
        # save back emf voltage magnitude here since it doesn't have a dynamic model in this generator model
        set_initial_conditions(self, 'E', E)
        return d


    def _dw_dt_model(self, Vpolar, current_states=None):
        if current_states is None:
            d, w, P = self._get_current_state_array()
        else:
            d, w, P = self._parse_state_array(current_states)

        # should this be wref = w, or wref = self.wnom
        if self.reference_angular_velocity is None:
            wref = self.wnom
        else:
            wref = self.reference_angular_velocity

        Pout = self._p_out_model(Vpolar, d=d)

        return (1./self.M)*(P - Pout - self.D*(w - wref))
        

    def _w0_model(self):
        return self.wnom

        
    def _dP_dt_model(self, Vpolar, current_states=None, current_setpoints=None):
        if current_states is None:
            _, w, P = self._get_current_state_array()
        else:
            _, w, P = self._parse_state_array(current_states)

        if current_setpoints is None:
            u = self.get_current_setpoints()[0]
        else:
            u = self._parse_state_array(current_setpoints)

        if self.reference_angular_velocity is None:
            wref = self.wnom
        else:
            wref = self.reference_angular_velocity

        return (1./self.taug)*(u - P - (1./(self.Rd*wref))*(w - wref))


    def _P0_model(self, Snetwork):
        
        return Pnetwork

        
    def _p_out_model(self, Vpolar, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        V, theta = Vpolar
        return (1./self.Xdp)*self.E[-1]*V*sin(d - theta)
        
        
    def _q_out_model(self, Vpolar, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        V, theta = Vpolar
        return (1./self.Xdp)*(self.E[-1]*V*cos(theta - d) - V**2)


    def _dp_out_d_theta_model(self, Vpolar, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        V, theta = Vpolar
        return -1*(1./self.Xdp)*V*self.E[-1]*cos(d - theta)


    def _dp_out_d_v_model(self, Vpolar, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        _, theta = Vpolar
        return (1./self.Xdp)*self.E[-1]*sin(d - theta)
        
    
    def dp_out_d_d_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*V*self.E[-1]*cos(d - theta)


    def _dq_out_d_theta_model(self, Vpolar, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        V, theta = Vpolar
        return -1*(1./self.Xdp)*V*self.E[-1]*sin(theta - d)
        
        
    def _dq_out_d_v_model(self, Vpolar, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        V, theta = Vpolar
        return (1./self.Xdp)*self.E[-1]*cos(theta - d) - 2*V/self.Xdp

        
    def dq_out_d_d_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*V*self.E[-1]*sin(theta - d)

        
    def _back_emf_initial_value(self, Vpolar, Pg, Qg):
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
        