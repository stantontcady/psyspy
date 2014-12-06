from itertools import count

from .power_line_impedance_change import PowerLineImpedanceChange


class TemporaryPowerLineImpedanceChange(PowerLineImpedanceChange):
    _temporary_power_line_impedance_change_ids = count(0)
    
    def __init__(self, affected_line, start_time, end_time, new_z=(), new_y=()):
        
        PowerLineImpedanceChange.__init__(self, affected_line, start_time, end_time, new_z, new_y)
        
        self._temporary_power_line_impedance_change_id = self._temporary_power_line_impedance_change_ids.next() + 1
        
        self._change_type = 'temporary_power_line_impedance_change'
