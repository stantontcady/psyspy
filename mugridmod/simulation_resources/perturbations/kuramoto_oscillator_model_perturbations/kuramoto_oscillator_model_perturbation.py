
from ..perturbation import Perturbation
from microgrid_model.model_components.models.dynamic_models import KuramotoOscillatorModel

class KuramotoOscillatorModelPerturbation(Perturbation):
    
    def __init__(self, start_time, affected_model, end_time=None):
        if isinstance(affected_model, KuramotoOscillatorModel) is False:
            raise TypeError('provided model must be an instance of the KuramotoOscillatorModel type or a subclass thereof')
            
        Perturbation.__init__(self, start_time=start_time, affected_model=affected_model, end_time=end_time)
