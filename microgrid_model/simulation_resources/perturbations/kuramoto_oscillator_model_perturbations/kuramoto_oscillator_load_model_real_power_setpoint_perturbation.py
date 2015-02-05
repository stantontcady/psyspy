from logging import debug

from numpy import array

from kuramoto_oscillator_model_natural_frequency_perturbation import KuramotoOscillatorModelNaturalFrequencyPerturbation


class KuramotoOscillatorLoadModelRealPowerSetpointPerturbation(KuramotoOscillatorModelNaturalFrequencyPerturbation):
    
    def __init__(self, start_time, affected_model, new_load, end_time=None):        
        KuramotoOscillatorModelNaturalFrequencyPerturbation.__init__(self,
                                                                     start_time=start_time,
                                                                     affected_model=affected_model,
                                                                     new_natural_frequency=-1.0*new_load,
                                                                     end_time=end_time)
        
        self._change_type = 'kuramoto_oscillator_load_model_real_power_setpoint_perturbation'
