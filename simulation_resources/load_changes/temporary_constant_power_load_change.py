from itertools import count

from .constant_power_load_change import ConstantPowerLoadChange


class TemporaryConstantPowerLoadChange(ConstantPowerLoadChange):
    _temporary_constant_power_load_change_ids = count(0)
    
    def __init__(self, affected_load, start_time, end_time, new_P=None, new_Q=None):

        ConstantPowerLoadChange.__init__(self, affected_load, start_time, end_time, new_P, new_Q)
        
        self._temporary_constant_power_load_change_id = self._temporary_constant_power_load_change_ids.next() + 1
        
        self._change_type = 'temporary_constant_power_load_change'
