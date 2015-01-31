

from ..model_change import ModelChange
from microgrid_model.model_components.models import KuramotoOscillatorModel

class KuramotoOscillatorModelChange(ModelChange):
    
    def __init__(self, affected_model, start_time, end_time=None):
        if isinstance(affected_model, KuramotoOscillatorModel) is False:
            raise TypeError('provided model must an instance of the KuramotoOscillatorModel type or a subclass thereof')
            
        ModelChange.__init__(self, affected_model=affected_model, start_time=start_time, end_time=end_time)
