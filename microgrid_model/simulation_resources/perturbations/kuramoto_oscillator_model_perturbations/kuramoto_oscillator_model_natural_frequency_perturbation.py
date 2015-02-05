from logging import debug

from numpy import array

from kuramoto_oscillator_model_perturbation import KuramotoOscillatorModelPerturbation


class KuramotoOscillatorModelNaturalFrequencyPerturbation(KuramotoOscillatorModelPerturbation):
    
    def __init__(self, start_time, affected_model, new_natural_frequency, end_time=None):        
        KuramotoOscillatorModelPerturbation.__init__(self, start_time=start_time, affected_model=affected_model, end_time=end_time)

        old_natural_frequency = affected_model._get_current_setpoint_array()[0]
        
        if new_natural_frequency == old_natural_frequency:
            debug('New natural frequency matches the current one, change will be disabled')
            self.enabled = False
        else:
            self.old_natural_frequency = old_natural_frequency
            self.new_natural_frequency = new_natural_frequency
        
        self._change_type = 'kuramoto_oscillator_model_natural_frequency_perturbation'


    def _activate(self):
        # no need to try / except for the following method as only KuramotoOscillatorModel affected_models are allowed
        self.affected_model.change_dynamic_model_real_power_setpoint(self.new_natural_frequency)


    def _deactivate(self):
        self.affected_model.change_dynamic_model_real_power_setpoint(self.old_natural_frequency)
