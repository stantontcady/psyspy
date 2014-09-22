from inspect import currentframe, getargvalues
from itertools import count
from math import pi
from numpy import append, array, empty

from model_components import set_initial_conditions, set_parameter_value
from dgr import DGR

class SynchronousDGR(DGR):
    
    _synchronous_dgr_ids = count(0)
    
    def __init__(V0=None, theta0=None, model='classical'):
                 
        super(DGR, self).__init__(V0, theta0)
        
        self._synchronous_dgr_id = self._synchronous_dgr_ids.next() + 1
        if model == 'classical':
            self.generator_model = ClassicalModel()
            
    
    def get_generator_incremental_states():
        pass
    

    
class ClassicalModel(object):
    
    def __init__(self,
                 wnom=None,
                 M=None,
                 D=None,
                 taug=None,
                 Rd=None,
                 R=None,
                 X=None,
                 u0=None,
                 d0=None,
                 w0=None,
                 P0=None,
                 E0=None):
        
        # TO DO: get reasonable defaults for machine params
        self.parameter_defaults = {
            'wnom' : 2*pi*60,
            'M' : 1,
            'D' : 0.1,
            'taug' : 0.1,
            'Rd' : 1,
            'R' : 0,
            'X' : 0.1
        }
        _, _, _, arg_values = getargvalues(currentframe())
        
        for parameter, default_value in self.parameter_defaults.iteritems():
            value = arg_values[parameter]
            if value is None:
                value = default_value
            set_parameter_value(self, parameter, value)
        
        # generator set-point
        set_initial_conditions(self, 'u', u0)
        # torque angle
        set_initial_conditions(self, 'd', d0)
        # speed
        set_initial_conditions(self, 'w', w0)
        # power output
        set_initial_conditions(self, 'P', P0)
        # back EMF
        set_initial_conditions(self, 'E', E0)
    
    def __repr__(self, simple=False, base_indent=0):
        indent_level_increment = 2
        
        object_info = []
        current_states = []
        parameters = []
        
        if simple is False:
            current_states.append('Voltage magnitude, V: %0.3f pu' % (self.V[-1]))
            current_states.append('Voltage angle, %s : %0.4f rad' % (u'\u03B8'.encode('UTF-8'), self.theta[-1]))
            
            parameters.append('Nominal frequency, %s_nom: %0.3f' % (u'\u03C9'.encode('UTF-8'), self.wnom))
            parameters.append('Moment of inertia, M: %0.3f' % (self.M))
            parameters.append('Damping coefficient, D: %0.3f' % (self.D))
            parameters.append('Governor time constant, %s_g: %0.3f' % (u'\u03C4'.encode('UTF-8'), self.taug))
            parameters.append('Droop coefficient, Rd: %0.3f' % (self.Rd))
            parameters.append('Generator resistance, R: %0.3f' % (self.R))
            parameters.append('Generator reactance, X: %0.3f' % (self.X))
            
        current_states.append('Back EMF, E: %0.3f' % (self.E[-1]))
        current_states.append('Torque angle, %s : %0.3f' % (u'\u03B4'.encode('UTF-8'), self.d[-1]))
        current_states.append('Angular speed, %s : %0.3f' % (u'\u03C9'.encode('UTF-8'), self.w[-1]))
        current_states.append('Power output, P: %0.3f' % (self.P[-1]))
        current_states.append('Set-point, u: %0.3f' % (self.u[-1]))
        
        object_info.append('<Synchronous DGR #%i, Classical Model>' % (self._synchronous_dgr_id))
        if current_states != []:
            object_info.append('%sCurrent state values:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), state) for state in current_states])
        if parameters != []:
            object_info.append('%sParameters:' % (''.rjust(indent_level_increment)))
            object_info.extend(['%s%s' % (''.rjust(2*indent_level_increment), parameter) for parameter in parameters])
            
        return '\n'.join(['%s%s' % ((''.rjust(base_indent), line)) for line in object_info])
        
    def d_incremental_model(self, w):
        return w - self.wnom
        
    def w_incremental_model(self, P, Pout, w):
        return (1./self.M)*(-1*self.D*(w - self.wnom)) + P - Pout
        
    def P_incremental_model(self, P, u, w):
        return (1./self.taug)*(-P - 1./(self.Rd*self.wnom)*(w - wnom) + u)
    
    def dynamic_state_incremental_model(self, inputs, states=None):
        if states is None:
            [d, w, P] = self.get_current_states()
        
        u = get_current_set_point()

        d_d = self.classical_d_incremental_model(w)
        d_w = self.classical_w_incremental_model(P, Pout, w)
        d_P = self.classical_P_incremental_model(P, u, w)
        
        return array([d_d, d_w, d_P])
        
    def get_current_states(self):
        return array(self.d[-1], self.w[-1], self.P[-1])
        
    def get_current_set_point(self):
        return self.u[-1]
        
    def update_states(self, states):
        [d, w, P] = states
        self.d = append(self.d, d)
        self.w = append(self.w, w)
        self.P = append(self.P, P)
        return self.get_current_states()
        
    def update_set_point(self, u):
        self.u = append(self.u, u)
        return self.get_current_set_point()
        
