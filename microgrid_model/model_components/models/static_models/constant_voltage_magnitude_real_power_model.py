
from ...helper_functions import set_initial_conditions
from .static_model import StaticModel


class ConstantVoltageMagnitudeRealPowerModel(StaticModel):
    
    def __init__(self, P=None):
        set_initial_conditions(self, 'P', P)
        
        StaticModel.__init__(self, voltage_magnitude_static=True, voltage_angle_static=False)


    def _get_real_power_injection(self, Vpolar):
        return self.P[-1]