from itertools import count

from .transient import Transient


class TemporaryPowerLineChange(Transient):
    _temporary_power_line_change_ids = count(0)
    
    def __init__(self, start_time, end_time, affected_line):
        
        Transient.__init__(self, start_time, end_time)
        
        self._temporary_power_line_change_id = self._temporary_power_line_change_ids.next() + 1
        
        self._change_type = 'temporary_power_line_change'
        
        self.affected_line = affected_line
