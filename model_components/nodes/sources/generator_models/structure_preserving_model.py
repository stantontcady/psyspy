from inspect import currentframe, getargvalues
from operator import itemgetter
from numpy import append, empty, nan
from math import asin, atan, cos, pi, sin, sqrt

from generator_model import GeneratorModel
from model_components import set_initial_conditions

from IPython import embed

class StructurePreservingModel(GeneratorModel):
    
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

        self.state_indicies = {
            'd' : 0,
            'w' : 1,
            'P' : 2
        }
        
        self.setpoint_indicies = {
            'u' : 0
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

        _, _, _, arg_values = getargvalues(currentframe())
        
        GeneratorModel.__init__(self, arg_values)
        
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

    
    def _d_incremental_model(self, V, theta, wref=None, current_states=None, current_setpoints=None):
        if current_states is None:
            current_states = self.get_current_states()
        
        _, w, _ = self.parse_state_vector(current_states)
        
        if wref is None:
            # if no reference angular velocity we assume this is the reference node
            wref = self.wnom

        return w - wref

        
    def _d_initial_value(self, V, theta, Pnetwork, Qnetwork, current_setpoints=None):
        E, d = self._back_emf_initial_value(V, theta, Pnetwork, Qnetwork)
        # save back emf voltage magnitude here since it doesn't have a dynamic model in this generator model
        set_initial_conditions(self, 'E', E)
        return d


    def _w_incremental_model(self, V, theta, wref=None, current_states=None, current_setpoints=None):
        if current_states is None:
            current_states = self.get_current_states()
            
        d, w, P = self.parse_state_vector(current_states)
        
        # dp stand for d prime, i.e., d'
        if self.reference_angle is None:
            raise AttributeError('reference angle is needed to get incremental state for angular velocity')
        # dp = d - self.reference_angle

        # should this be wref = w, or wref = self.wnom
        if self.reference_angular_velocity is None:
            wref = self.wnom
        else:
            wref = self.reference_angular_velocity
        
        Pout = self.p_out_model(V, theta, d)
        
        return (1./self.M)*(P - Pout - self.D*(w - wref))
        

    def _w_initial_value(self, V, theta, Pnetwork=None, Qnetwork=None, current_setpoints=None):
        return self.wnom

        
    def _P_incremental_model(self, V, theta, current_states=None, current_setpoints=None):
        if current_states is None:
            current_states = self.get_current_states()
            
        _, w, P = self.parse_state_vector(current_states)
        
        if current_setpoints is None:
            current_setpoints = self.get_current_setpoints()
            
        u, = self.parse_setpoint_vector(current_setpoints)
        
        if self.reference_angular_velocity is None:
            wref = self.wnom
        else:
            wref = self.reference_angular_velocity
        
        return (1./self.taug)*(u - P - (1./(self.Rd*wref))*(w - wref))


    def _P_initial_value(self, V, theta, Pnetwork=None, Qnetwork=None, current_setpoints=None):
        if current_setpoints is None:
            current_setpoints = self.get_current_setpoints()
            
        # u, = self.parse_setpoint_vector(current_setpoints)
        return Pnetwork

        
    def p_out_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*self.E[-1]*V*sin(d - theta)
        
        
    def q_out_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*(self.E[-1]*V*cos(theta - d) - V**2)


    def dp_out_d_theta_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return -1*(1./self.Xdp)*V*self.E[-1]*cos(d - theta)


    def dp_out_d_v_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*self.E[-1]*sin(d - theta)
        
    
    def dp_out_d_d_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*V*self.E[-1]*cos(d - theta)


    def dq_out_d_theta_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return -1*(1./self.Xdp)*V*self.E[-1]*sin(theta - d)
        
        
    def dq_out_d_v_model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*self.E[-1]*cos(theta - d) - 2*V/self.Xdp

        
    def dq_out_d__model(self, V, theta, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        return (1./self.Xdp)*V*self.E[-1]*sin(theta - d)

        
    def _back_emf_initial_value(self, V, theta, Pg, Qg):
        # these are needed numerous times, compute once first
        cos_theta = cos(theta)
        sin_theta = sin(theta)
        # Back emf is E < delta = a + jb
        a = V*cos_theta + self.Xdp*(Qg*cos_theta - Pg*sin_theta)/V
        b = V*sin_theta + self.Xdp*(Pg*cos_theta + Qg*sin_theta)/V
        
        E = sqrt(a**2 + b**2)
        delta = atan(b/a)
        
        return E, delta
        