from kuramoto_oscillator_model import KuramotoOscillatorModel


class KuramotoOscillatorGeneratorModel(KuramotoOscillatorModel):
    
    def __init__(self, parameters, initial_setpoint):
                 
        KuramotoOscillatorModel.__init__(self,
										 parameters,
										 initial_setpoint=initial_setpoint,
										 is_generator=True, is_load=False)
                 
        self.model_type = {
            'simple_name':'kuramoto_oscillator_generator',
            'full_name':'Kuramoto Oscillator Dynamic Generator Model'
        }
