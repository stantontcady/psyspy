

from numpy import append

from .bus import Bus
from ..models.static_models import ConstantApparentPowerModel


class PQBus(Bus):
    
    def __init__(self, P=None, Q=None, V0=None, theta0=None, shunt_z=(), shunt_y=(), name=None):
        
        model = ConstantApparentPowerModel(P=P, Q=Q)
        
        Bus.__init__(self, model=model, V0=V0, theta0=theta0, shunt_z=shunt_z, shunt_y=shunt_y, name=name)


