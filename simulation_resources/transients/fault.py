

from .transient import Transient

class TemporaryFault(Transient):
    _temporary_fault_ids = count(0)
    
    def __init__(self, start_time, end_time):
        
        Transient.__init__(self, start_time, end_time)
        
        self._temporary_fault_id = self._temporary_fault_ids.next() + 1
        
        self._change_type = 'temporary_fault'
