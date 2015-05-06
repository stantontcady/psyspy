

from ..model import Model


class StaticModel(Model):
    
    def __init__(self, voltage_magnitude_static=False, voltage_angle_static=False):

        Model.__init__(self, voltage_magnitude_static=voltage_magnitude_static, voltage_angle_static=voltage_angle_static)
