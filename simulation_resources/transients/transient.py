from itertools import count

from ..system_change import SystemChange


class Transient(SystemChange):
    _transient_ids = count(0)
    
    def __init__(self, start_time, end_time):
        
        SystemChange.__init__(self, start_time, end_time)
        
        self._transient_id = self._transient_ids.next() + 1
        
        self._change_type = 'transient'
        
