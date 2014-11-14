

from .system_change import SystemChange

class PermanentFault(SystemChange):
    _permanent_fault_ids = count(0)
    
    def __init__(self, start_time):
        
        SystemChange.__init__(self, start_time, end_time=None)
        
        self._permanent_fault_id = self._permanent_fault_ids.next() + 1
        
        self._change_type = 'permanent_fault'
