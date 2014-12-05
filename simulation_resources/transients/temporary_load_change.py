from itertools import count

from .transient import Transient


class TemporaryLoadChange(Transient):
    _temporary_load_change_ids = count(0)
    
    def __init__(self, start_time, end_time, affected_load):
        
        Transient.__init__(self, start_time, end_time)
        
        self._temporary_load_change_id = self._temporary_load_change_ids.next() + 1
        
        self._change_type = 'temporary_load_change'
        
        self.affected_load = affected_load
