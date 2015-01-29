
from ...helper_functions import set_initial_conditions
from .static_model import StaticModel


class ConstantApparentPowerModel(StaticModel):
    
    def __init__(self, P=None, Q=None):
        set_initial_conditions(self, 'P', P)
        set_initial_conditions(self, 'Q', Q)
        
        StaticModel.__init__(self, voltage_magnitude_static=False, voltage_angle_static=False)
        

    def _get_real_power_injection(self, Vpolar):
        # negating the value since injections are defined to be positive
        return -1*self.P[-1]


    def _get_reactive_power_injection(self, Vpolar):
        # negating the value since injections are defined to be positive
        return -1*self.Q[-1]