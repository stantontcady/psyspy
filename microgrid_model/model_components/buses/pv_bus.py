
from .bus import Bus
from ..models.static_models import ConstantVoltageMagnitudeRealPowerModel


class PVBus(Bus):
    
    def __init__(self, P=None, V=None, theta0=None, shunt_z=(), shunt_y=(), name=None):
        
        model = ConstantVoltageMagnitudeRealPowerModel(P=P)
        
        Bus.__init__(self, model=model, V0=V, theta0=theta0, shunt_z=shunt_z, shunt_y=shunt_y, name=name)
        
        self._bus_type = 'pv_bus'

