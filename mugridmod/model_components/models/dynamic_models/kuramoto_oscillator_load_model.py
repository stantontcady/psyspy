from kuramoto_oscillator_model import KuramotoOscillatorModel


class KuramotoOscillatorLoadModel(KuramotoOscillatorModel):
    
    def __init__(self, parameters, initial_load):
                 
        KuramotoOscillatorModel.__init__(self,
										 parameters,
										 initial_setpoint=-1.0*initial_load,
										 is_generator=False, is_load=True)
                 
        self.model_type = {
            'simple_name':'kuramoto_oscillator_load',
            'full_name':'Kuramoto Oscillator Dynamic Load Model'
        }
        