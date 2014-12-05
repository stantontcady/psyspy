from itertools import count

from .permanent_fault import PermanentFault


class PermanentLoadChange(PermanentFault):
    _permanent_load_change_ids = count(0)
    
    def __init__(self, start_time, affected_load):
        
        PermanentFault.__init__(self, start_time)
        
        self._permanent_load_change_id = self._permanent_load_change_ids.next() + 1
        
        self._change_type = 'permanent_load_change'
        
        self.affected_load = affected_load
