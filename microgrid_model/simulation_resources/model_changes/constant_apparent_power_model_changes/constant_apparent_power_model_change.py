

from ..model_change import ModelChange
from microgrid_model.model_components.models import ConstantApparentPowerModel

class ConstantApparentPowerModelChange(ModelChange):
    
    def __init__(self, start_time, affected_model, end_time=None):
        if isinstance(affected_model, ConstantApparentPowerModel) is False:
            raise TypeError('provided model must an instance of the ConstantApparentPowerModel type or a subclass thereof')
            
        ModelChange.__init__(self, start_time=start_time, affected_model=affected_model, end_time=end_time)
