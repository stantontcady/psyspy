from inspect import currentframe, getargvalues
from operator import itemgetter
from numpy import append, empty, nan
from math import pi

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
                 u0=None,
                 d0=None,
                 w0=None,
                 P0=None,
                 E0=None):
                 
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
            'X' : 0.1
        }

        _, _, _, arg_values = getargvalues(currentframe())
        
        GeneratorModel.__init__(self, arg_values)
        
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
    
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])

        
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
            
        current_states.append('Back EMF, E: %0.3f' % (self.E[-1]))
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

        
    def get_current_set_points(self):
        return array([self.u[-1]])


    def update_set_point(self, u):
        self.u = append(self.u, u)
        return self.get_current_set_point()

    
    def _d_incremental_model(self, w):
        return w - self.wnom
        
    def _w_incremental_model(self, P, Pout, w):
        return (1./self.M)*(-1*self.D*(w - self.wnom)) + P - Pout
        
    def _P_incremental_model(self, P, u, w):
        return (1./self.taug)*(-P - 1./(self.Rd*self.wnom)*(w - wnom) + u)
