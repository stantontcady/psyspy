from numpy import append

from microgrid_model.helper_functions import set_initial_conditions
from static_model import StaticModel


class ConstantApparentPowerModel(StaticModel):
    
    def __init__(self, P=None, Q=None):
        set_initial_conditions(self, 'P', P)
        set_initial_conditions(self, 'Q', Q)
        
        StaticModel.__init__(self, voltage_magnitude_static=False, voltage_angle_static=False)
        

    def _get_real_power_injection(self):
        # negating the value since injections are defined to be positive
        return -1.0*self.P[-1]


    def _get_reactive_power_injection(self):
        # negating the value since injections are defined to be positive
        return -1.0*self.Q[-1]
        
    
    def change_real_power_injection(self, new_P, replace=False):
        if replace is False:
            self.P = append(self.P, new_P)
        else:
            self.P[-1] = new_P
        
        return self._get_real_power_injection()


    def change_reactive_power_injection(self, new_Q, replace=False):
        if replace is False:
            self.Q = append(self.Q, new_Q)
        else:
            self.Q[-1] = new_Q
        
        return self._get_reactive_power_injection()
