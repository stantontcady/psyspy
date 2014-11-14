from itertools import count

from .power_line_change import TemporaryPowerLineChange


class TemporaryPowerLineImpedanceChange(TemporaryPowerLineChange):
    _temporary_power_line_impedance_change_ids = count(0)
    
    def __init__(self, start_time, end_time, affected_line, new_z=(), new_y=()):
        
        # check for constant power line impedance change-specific errors before calling super class init
        if new_z == () and new_y == ():
            raise StandardError('A new reacatance or admittance must be specified for power line impedance change')
        
        TemporaryPowerLineChange.__init__(self, start_time, end_time, affected_line)
        
        self._temporary_power_line_impedance_change_id = self._temporary_power_line_impedance_change_ids.next() + 1
        
        self._change_type = 'temporary_power_line_impedance_change'

