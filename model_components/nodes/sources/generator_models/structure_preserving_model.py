from inspect import currentframe, getargvalues
from operator import itemgetter
from numpy import append, empty, nan
from math import asin, cos, pi, sin

from generator_model import GeneratorModel
from model_components import set_initial_conditions

class StructurePreservingModel(GeneratorModel):
    
    def __init__(self,
                 wnom=None,
                 H=None,
                 M=None,
                 D=None,
                 taug=None,
                 Rd=None,
                 R=None,
                 X=None,
                 E=None,
                 u0=None):
                 
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
            'X' : 0.1,
            'E' : 1
        }

        _, _, _, arg_values = getargvalues(currentframe())
        
        GeneratorModel.__init__(self, arg_values)
        
        # generator set-point
        set_initial_conditions(self, 'u', u0)

        
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
            parameters.append('Generator reactance, X: %0.3f' % (self.X))
            
        current_states.append('Back EMF, E: %0.3f' % (self.E))
        current_states.append('Torque angle, %s : %0.3f' % (u'\u03B4'.encode('UTF-8'), self.d[-1]))
        current_states.append('Angular speed, %s : %0.3f' % (u'\u03C9'.encode('UTF-8'), self.w[-1]))
        current_states.append('Power output, P: %0.3f' % (self.P[-1]))
        current_states.append('Set-point, u: %0.3f' % (self.u[-1]))
        
        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
            
        return object_info

    
    def _d_incremental_model(self, V, theta, current_states=None, current_setpoints=None):
        if current_states is None:
            current_states = self.get_current_states()
        
        _, w, _ = self.parse_state_vector(current_states)
        
        return w - self.wnom

        
    def _d_initial_value(self, V, theta, current_setpoints=None):
        if current_setpoints is None:
            current_setpoints = self.get_current_setpoints()
            
        u, = self.parse_setpoint_vector(current_setpoints)
        
        return theta + asin((self.X*u)/(self.E*V))


    def _w_incremental_model(self, V, theta, current_states=None, current_setpoints=None):
        if current_states is None:
            current_states = self.get_current_states()
            
        d, w, P = self.parse_state_vector(current_states)
        
        Pout = self._Pout_model(V, theta, d)
        
        return (1./self.M)*(P - Pout - self.D*(w - self.wnom))
        

    def _w_initial_value(self, V, theta, current_setpoints=None):
        return self.wnom

        
    def _P_incremental_model(self, V, theta, current_states=None, current_setpoints=None):
        if current_states is None:
            current_states = self.get_current_states()
            
        _, w, P = self.parse_state_vector(current_states)
        
        if current_setpoints is None:
            current_setpoints = self.get_current_setpoints()
            
        u, = self.parse_setpoint_vector(current_setpoints)
        
        return (1./self.taug)*(u - P - (1./(self.Rd*self.wnom))*(w - self.wnom))


    def _P_initial_value(self, V, theta, current_setpoints=None):
        if current_setpoints is None:
            current_setpoints = self.get_current_setpoints()
            
        u, = self.parse_setpoint_vector(current_setpoints)
        
        return u

        
    def _Pout_model(self, V, theta, d=None):
        if d is None:
            current_states = self.get_current_states(as_dictionary=True)
            d = current_states['d']
        return (1./self.X)*self.E*V*sin(d - theta)
        
        
    def _Qout_model(self, V, theta, d=None):
        if d is None:
            current_states = self.get_current_states(as_dictionary=True)
            d = current_states['d']
        return (1./self.X)*(self.E*V*cos(d - theta) - V**2)
