from logging import debug

from constant_apparent_power_model_change import ConstantApparentPowerModelChange


class ConstantApparentPowerModelApparentPowerInjectionChange(ConstantApparentPowerModelChange):
    
    def __init__(self, start_time, affected_model, new_P=None, new_Q=None, end_time=None):        
        ConstantApparentPowerModelChange.__init__(self, affected_model=affected_model, start_time=start_time, end_time=end_time)

        self.old_P = affected_model.P[-1]
        self.old_Q = affected_model.Q[-1]
        
        self.real_power_change_enabled = False
        if self.old_P == new_P:
            debug('New real power is identical to current value, change will have no effect')
        elif new_P is not None:
            self.real_power_change_enabled = True
            self.new_P = new_P

        self.reactive_power_change_enabled = False
        if self.old_Q == new_Q:
            debug('New reactive power is identical to current value, change will have no effect')
        elif new_Q is not None:
            self.reactive_power_change_enabled = True
            self.new_Q = new_Q
            
        if self.real_power_change_enabled is False and self.reactive_power_change_enabled is False:
            self.enabled = False
            debug('Specified apparent power change is identical to current value, change is disabled')

        self._change_type = 'constant_apparent_power_model_apparent_power_injection_change'


    def _activate_model_change(self):
        if self.real_power_change_enabled is True:
            self.affected_model.change_real_power_injection(self.new_P)

        if self.reactive_power_change_enabled is True:
            self.affected_model.change_reactive_power_injection(self.new_Q)


    def _deactivate_model_change(self):
        if self.real_power_change_enabled is True:
            self.affected_model.change_real_power_injection(self.old_P)

        if self.reactive_power_change_enabled is True:
            self.affected_model.change_reactive_power_injection(self.old_Q)
