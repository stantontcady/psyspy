from itertools import count

from ..system_change import SystemChange


class PowerLineChange(SystemChange):
    _power_line_change_ids = count(0)
    
    def __init__(self, affected_line, start_time, end_time):
        
        SystemChange.__init__(self, start_time, end_time)
        
        self._power_line_change_id = self._power_line_change_ids.next() + 1
        
        self._change_type = 'power_line_change'
        
        self.affected_line = affected_line
