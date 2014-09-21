from inspect import currentframe, getargvalues
from itertools import count
from math import pi
from numpy import empty, append

from helper_functions import set_initial_conditions, set_parameter_value
from dgr import DGR

class synchronous_generator(DGR):
    
    _synchronous_generator_ids = count(0)
    
    def __init__(self,
                 wref=None,
                 M=None,
                 D=None,
                 taug=None,
                 Rg=None,
                 R=None,
                 X=None,
                 u0=None,
                 d0=None,
                 w0=None,
                 P0=None,
                 E0=None,
                 V0=None,
                 theta0=None):
                 
        super(DGR, self).__init__(V0, theta0)
        
        self.synchronous_generator_id = self._synchronous_generator_ids.next() + 1
        
        # TO DO: get reasonable defaults for machine params
        self.parameter_defaults = {
            'wref' : 2*pi*60,
            'M' : 0,
            'D' : 0,
            'taug' : 0,
            'Rg' : 0,
            'R' : 0,
            'X' : 0
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
        indent = ''
        indent_level_increment = 2
        object_description = '%s<Synchronous Distributed Generation Resource #%i>' % (indent.rjust(base_indent),
                                                                                      self.synchronous_generator_id)
        E = '%sBack EMF, E: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.E[-1])
        d = '%sTorque angle, %s : %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment),
                                            u'\u03B4'.encode('UTF-8'),
                                            self.E[-1])
        w = '%sAngular speed, %s : %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment),
                                             u'\u03C9'.encode('UTF-8'), self.w[-1])
        P = '%sPower output, P: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.P[-1])
        u = '%sSet-point, u: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.u[-1])

        if simple is False:
            V = '%sVoltage magnitude, V: %0.3f pu' % (indent.rjust(base_indent + 2*indent_level_increment), self.V[-1])
            theta = '%sVoltage angle, %s : %0.4f rad' % (indent.rjust(base_indent + 2*indent_level_increment),
                                                         u'\u03B8'.encode('UTF-8'), self.theta[-1])
            current_states = '%sCurrent state values:\n%s\n%s\n%s\n%s\n%s\n%s\n%s' % (indent.rjust(base_indent + indent_level_increment),
                                                                                      V, theta, E, d, w, P, u)
            
            wref = '%sReference frequency, %s_ref: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment),
                                                             u'\u03C9'.encode('UTF-8'), self.wref)
            M = '%sMoment of inertia, M: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.M)
            D = '%sDamping coefficient, D: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.D)
            taug = '%sGovernor time constant, %s_g: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment),
                                                              u'\u03C4'.encode('UTF-8'), self.taug)
            Rg = '%sDroop coefficient, Rg: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.Rg)
            R = '%sGenerator resistance, R: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.R)
            X = '%sGenerator reactance, X: %0.3f' % (indent.rjust(base_indent + 2*indent_level_increment), self.X)
            parameters = '%sParameters:\n%s\n%s\n%s\n%s\n%s\n%s\n%s' % (indent.rjust(base_indent + indent_level_increment),
                                                                        wref, M, D, taug, Rg, R, X)
            
            return '%s\n%s\n\n%s' % (object_description, current_states, parameters)
        else:
            current_states = '%sCurrent state values:\n%s\n%s\n%s\n%s\n%s' % (indent.rjust(base_indent + indent_level_increment),
                                                                              E, d, w, P, u)
            
            return '%s\n%s' % (object_description, current_states)